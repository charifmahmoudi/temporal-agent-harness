"""Independent adaptation of public issue #673; development reproduction only."""
import argparse
import asyncio
import base64
from datetime import timedelta
import gzip
import hashlib
import json
from pathlib import Path
import platform
import uuid

import temporalio
from temporalio import activity, workflow
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Replayer, Worker, UnsandboxedWorkflowRunner


@activity.defn
async def recovery_echo() -> str:
    return 'completed'


@workflow.defn
class RecoveryBoundaryProbe:
    def __init__(self):
        self.inflight = 0
        self.finished = 0

    @workflow.run
    async def run(self) -> int:
        await asyncio.sleep(3)
        return self.finished

    async def perform(self):
        self.inflight += 1
        await workflow.execute_activity(recovery_echo,
            start_to_close_timeout=timedelta(seconds=10))
        self.inflight -= 1
        self.finished += 1

    @workflow.signal
    async def begin(self):
        await self.perform()

    @workflow.update
    async def resume(self) -> bool:
        if self.inflight:
            return False
        await self.perform()
        return True


def digest(data):
    return hashlib.sha256(data).hexdigest()


def classify(live_ok, failure):
    if not live_ok:
        return 'inconclusive_live_precondition'
    if failure is None:
        return 'compatible'
    if isinstance(failure, workflow.NondeterminismError):
        return 'nondeterministic'
    return 'inconclusive_replay_error'


async def trial(env, delay, out):
    queue = 'recovery-673-' + uuid.uuid4().hex
    async with Worker(env.client, task_queue=queue, workflows=[RecoveryBoundaryProbe],
                      activities=[recovery_echo], workflow_runner=UnsandboxedWorkflowRunner()):
        handle = await env.client.start_workflow(RecoveryBoundaryProbe.run,
            id=queue, task_queue=queue, execution_timeout=timedelta(seconds=30))
        await handle.signal(RecoveryBoundaryProbe.begin)
        await asyncio.sleep(delay)
        resumed = await handle.execute_update(RecoveryBoundaryProbe.resume)
        finished = await handle.result()
    history = await handle.fetch_history()
    raw = history.to_json().encode()
    name = f'history-{delay}.json'
    (out / name).write_bytes(raw)
    events = json.loads(raw)['events']
    scheduled = [int(e['eventId']) for e in events
                 if 'activityTaskScheduledEventAttributes' in e]
    completed = [int(e['eventId']) for e in events
                 if 'activityTaskCompletedEventAttributes' in e]
    update = [e['workflowExecutionUpdateAcceptedEventAttributes'] for e in events
              if 'workflowExecutionUpdateAcceptedEventAttributes' in e]
    failure = None
    try:
        await Replayer(workflows=[RecoveryBoundaryProbe],
                       workflow_runner=UnsandboxedWorkflowRunner()).replay_workflow(history)
    except Exception as exc:
        failure = exc
    live_ok = resumed is True and finished == 2 and len(scheduled) == len(completed) == 2
    result = {'delay_seconds': delay, 'resumed': resumed, 'finished': finished,
        'scheduled_event_ids': scheduled, 'completed_event_ids': completed,
        'update_acceptance': update, 'history_file': name, 'history_sha256': digest(raw),
        'verdict': classify(live_ok, failure),
        'exception_type': type(failure).__name__ if failure else None,
        'exception': str(failure) if failure else None}
    # Small complete history evidence survives even if artifact download is unavailable.
    print('RECOVERY_HISTORY ' + json.dumps({'name': name, 'sha256': digest(raw),
        'gzip_base64': base64.b64encode(gzip.compress(raw, mtime=0)).decode()}), flush=True)
    return result


async def run(args):
    args.output.mkdir(parents=True, exist_ok=True)
    report = {'schema': 1, 'issue': 'https://github.com/temporalio/sdk-python/issues/673',
        'sdk_version': temporalio.__version__, 'python': platform.python_version(),
        'script_sha256': digest(Path(__file__).read_bytes()),
        'sandbox': False, 'server': 'SDK default time-skipping test server',
        'cases': [], 'infrastructure_error': None}
    try:
        async with await WorkflowEnvironment.start_time_skipping(
                download_dest_dir=str(args.output)) as env:
            for delay in (0.1, 0.5, 1.0):
                report['cases'].append(await asyncio.wait_for(trial(env, delay, args.output), 60))
    except Exception as exc:
        report['infrastructure_error'] = {'type': type(exc).__name__, 'message': str(exc)}
    (args.output / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    print('RECOVERY_SUMMARY ' + json.dumps(report), flush=True)
    expected = 'nondeterministic' if args.expect == 'affected' else 'compatible'
    if report['infrastructure_error'] or len(report['cases']) != 3:
        raise SystemExit('Infrastructure or collection incomplete; no bug verdict')
    if any(c['verdict'] != expected for c in report['cases']):
        raise SystemExit('Observed outcomes differ from development prediction; retain evidence')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--expect', choices=('affected', 'fixed'), required=True)
    asyncio.run(run(parser.parse_args()))
