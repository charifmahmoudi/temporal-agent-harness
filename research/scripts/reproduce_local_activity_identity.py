"""Independent adapter of Python #1881; freshly recorded histories only."""
import argparse
import asyncio
from datetime import timedelta
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import uuid

import temporalio
from temporalio import activity, workflow
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Replayer, Worker, UnsandboxedWorkflowRunner


@activity.defn
async def identity_work(index: int) -> str:
    return str(index)


@activity.defn
async def identity_expired() -> bool:
    return False


@activity.defn
async def identity_finish() -> str:
    return "finished"


@workflow.defn
class IdentityFanout:
    @workflow.run
    async def run(self, local: bool) -> str:
        start = workflow.start_local_activity if local else workflow.start_activity
        execute = workflow.execute_local_activity if local else workflow.execute_activity
        tasks = {start(identity_work, i, start_to_close_timeout=timedelta(seconds=10)): i
                 for i in range(3)}
        pending = set(tasks)
        while pending:
            done, pending = await workflow.wait(pending, return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                assert await task == str(tasks[task]), "Result identity mismatch"
            if pending:
                assert await execute(identity_expired, start_to_close_timeout=timedelta(seconds=10)) is False
        return await execute(identity_finish, start_to_close_timeout=timedelta(seconds=10))


def exception_chain(error):
    chain, seen = [], set()
    while error is not None and id(error) not in seen:
        seen.add(id(error))
        chain.append({"type": type(error).__name__, "message": str(error)})
        error = error.__cause__ or error.__context__
    return chain


async def trial(env, local, directory):
    queue = "identity-" + uuid.uuid4().hex
    handle = None
    record = {"local": local}
    try:
        async with asyncio.timeout(30):
            async with Worker(env.client, task_queue=queue, workflows=[IdentityFanout],
                    activities=[identity_work, identity_expired, identity_finish],
                    workflow_runner=UnsandboxedWorkflowRunner()):
                handle = await env.client.start_workflow(IdentityFanout.run, local,
                    id=queue, task_queue=queue, execution_timeout=timedelta(seconds=25))
                result = await handle.result()
                assert result == "finished", "Unexpected final payload"
                record["live_result"] = result
        history = await handle.fetch_history()
        raw = history.to_json().encode()
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "history.json").write_bytes(raw)
        record["history_sha256"] = hashlib.sha256(raw).hexdigest()
        events = json.loads(raw)["events"]
        record["local_marker_count"] = sum(e.get("markerRecordedEventAttributes", {}).get("markerName") == "LocalActivity" for e in events)
        record["remote_schedule_count"] = sum("activityTaskScheduledEventAttributes" in e for e in events)
        try:
            async with asyncio.timeout(30):
                await Replayer(workflows=[IdentityFanout], workflow_runner=UnsandboxedWorkflowRunner()).replay_workflow(history)
            record.update(verdict="compatible", replay_exception=[])
        except Exception as error:
            chain = exception_chain(error)
            if isinstance(error, workflow.NondeterminismError):
                verdict = "typed_nondeterminism"
            elif any(e["type"] == "TypeError" and "Expected value to be str" in e["message"]
                     and "bool" in e["message"] for e in chain):
                verdict = "reported_decoding_mechanism"
            else:
                verdict = "inconclusive_replay_error"
            record.update(verdict=verdict, replay_exception=chain)
    except Exception as error:
        record.update(verdict="inconclusive_live_or_collection", live_exception=exception_chain(error))
        if handle is not None:
            try:
                history = await handle.fetch_history()
                directory.mkdir(parents=True, exist_ok=True)
                raw = history.to_json().encode()
                (directory / "history.json").write_bytes(raw)
                record["history_sha256"] = hashlib.sha256(raw).hexdigest()
            except Exception as collect_error:
                record["collection_exception"] = exception_chain(collect_error)
    return record


async def main(args):
    args.output.mkdir(parents=True, exist_ok=True)
    report = {"sdk": temporalio.__version__, "python": platform.python_version(),
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "server_sha256": hashlib.sha256(args.temporal.read_bytes()).hexdigest(),
        "cli_version": subprocess.check_output([str(args.temporal), "--version"], text=True).strip(),
        "rows": [], "infrastructure_error": None}
    try:
        async with await WorkflowEnvironment.start_local(dev_server_existing_path=str(args.temporal)) as env:
            for repetition in range(1, 4):
                for local in (True, False):
                    directory = args.output / f"r{repetition}-{'local' if local else 'remote'}"
                    row = await trial(env, local, directory)
                    row["repetition"] = repetition
                    report["rows"].append(row)
                    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
                    print(json.dumps(row), flush=True)
    except Exception as error:
        report["infrastructure_error"] = exception_chain(error)
    finally:
        (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--temporal", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.temporal = args.temporal.resolve()
    asyncio.run(main(args))
