"""Frozen development pilot: scheduled boundary probes versus two strong controls."""
import argparse
import asyncio
import base64
from datetime import timedelta
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import platform
import random
import time
import uuid

import temporalio
from temporalio import activity, workflow
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker, Replayer, UnsandboxedWorkflowRunner
from reproduce_recovery_673 import classify


@activity.defn
async def delayed_echo(delay: float) -> str:
    await asyncio.sleep(delay)
    return 'done'


@workflow.defn
class ScheduleProbe:
    def __init__(self):
        self.busy = 0
        self.finished = 0
        self.latency = 0.0

    @workflow.run
    async def run(self, latency: float) -> int:
        self.latency = latency
        await asyncio.sleep(3)
        return self.finished

    async def perform(self):
        self.busy += 1
        await workflow.execute_activity(delayed_echo, self.latency,
            start_to_close_timeout=timedelta(seconds=10))
        self.busy -= 1
        self.finished += 1

    @workflow.signal
    async def begin(self):
        await self.perform()

    @workflow.update
    async def resume(self) -> bool:
        if self.busy:
            return False
        await self.perform()
        return True


def plan():
    domain = list(itertools.product((0.0, 0.15), (0.0, 0.05, 0.2, 0.5)))
    systematic = [(0.15, 0.0), (0.0, 0.5), (0.15, 0.2), (0.0, 0.0)]
    return {str(seed): {'systematic': systematic,
        'random': random.Random(seed).sample(domain, 4),
        'regression': [(0.0, 0.5)] * 4} for seed in (0, 1, 2)}


async def trial(env, latency, delay):
    started = time.perf_counter()
    queue = 'schedule-' + uuid.uuid4().hex
    async with Worker(env.client, task_queue=queue, workflows=[ScheduleProbe],
            activities=[delayed_echo], workflow_runner=UnsandboxedWorkflowRunner()):
        handle = await env.client.start_workflow(ScheduleProbe.run, latency,
            id=queue, task_queue=queue, execution_timeout=timedelta(seconds=30))
        await handle.signal(ScheduleProbe.begin)
        await asyncio.sleep(delay)
        resumed = await handle.execute_update(ScheduleProbe.resume)
        finished = await handle.result()
    history = await handle.fetch_history()
    raw = history.to_json().encode()
    events = json.loads(raw)['events']
    schedules = [int(e['eventId']) for e in events if 'activityTaskScheduledEventAttributes' in e]
    completions = [int(e['eventId']) for e in events if 'activityTaskCompletedEventAttributes' in e]
    accepted = [e['workflowExecutionUpdateAcceptedEventAttributes'] for e in events
                if 'workflowExecutionUpdateAcceptedEventAttributes' in e]
    sequencing = int(accepted[0]['acceptedRequestSequencingEventId']) if len(accepted) == 1 else None
    expected = 2 if resumed is True else 1
    live_ok = isinstance(resumed, bool) and finished == expected and len(schedules) == len(completions) == expected
    failure = None
    replay_started = time.perf_counter()
    try:
        await Replayer(workflows=[ScheduleProbe], workflow_runner=UnsandboxedWorkflowRunner()).replay_workflow(history)
    except Exception as exc:
        failure = exc
    return {'latency': latency, 'update_delay': delay, 'resumed': resumed,
        'finished': finished, 'scheduled_ids': schedules, 'completed_ids': completions,
        'update_sequencing_id': sequencing,
        'coverage': [resumed, bool(completions and sequencing and completions[0] < sequencing)],
        'verdict': classify(live_ok, failure),
        'exception_type': type(failure).__name__ if failure else None,
        'exception': str(failure) if failure else None,
        'replay_seconds': time.perf_counter() - replay_started,
        'total_seconds': time.perf_counter() - started,
        'history_sha256': hashlib.sha256(raw).hexdigest(),
        'history_gzip_base64': base64.b64encode(gzip.compress(raw, mtime=0)).decode()}


async def main(args):
    args.output.mkdir(parents=True, exist_ok=True)
    args.server_dir.mkdir(parents=True, exist_ok=True)
    binaries = sorted(p for p in args.server_dir.iterdir() if p.is_file() and p.name.startswith('temporal-test-server'))
    if len(binaries) > 1:
        raise RuntimeError('Ambiguous server binaries')
    if args.require_existing and not binaries:
        raise RuntimeError('Shared server binary missing')
    report = {'sdk': temporalio.__version__, 'python': platform.python_version(),
        'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'plan': plan(), 'rows': [], 'infrastructure_error': None}
    started = time.perf_counter()
    try:
        async with await WorkflowEnvironment.start_time_skipping(
            test_server_existing_path=str(binaries[0]) if binaries else None,
            download_dest_dir=str(args.server_dir)) as env:
            binaries = sorted(p for p in args.server_dir.iterdir() if p.is_file() and p.name.startswith('temporal-test-server'))
            if len(binaries) != 1:
                raise RuntimeError('Cannot identify shared server binary')
            report['server_sha256'] = hashlib.sha256(binaries[0].read_bytes()).hexdigest()
            report['setup_seconds'] = time.perf_counter() - started
            methods = ['systematic', 'random', 'regression']
            for seed, schedules in plan().items():
                # Rotate execution order across repetitions to limit fixed order bias.
                offset = int(seed)
                order = methods[offset:] + methods[:offset]
                for index in range(4):
                    for method in order:
                        latency, delay = schedules[method][index]
                        try:
                            row = await asyncio.wait_for(trial(env, latency, delay), timeout=45)
                        except Exception as exc:
                            row = {'latency': latency, 'update_delay': delay,
                                'verdict': 'inconclusive_collection', 'exception_type': type(exc).__name__,
                                'exception': str(exc)}
                        row.update(seed=int(seed), method=method, index=index+1)
                        report['rows'].append(row)
                        print('SCHEDULE_ROW ' + json.dumps(row), flush=True)
    except Exception as exc:
        report['infrastructure_error'] = {'type': type(exc).__name__, 'message': str(exc)}
    report['total_seconds'] = time.perf_counter() - started
    (args.output / 'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print('SCHEDULE_REPORT ' + json.dumps(report), flush=True)
    if report['infrastructure_error'] or len(report['rows']) != 36:
        raise SystemExit('Incomplete collection; retain observations')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--server-dir', type=Path, required=True)
    parser.add_argument('--require-existing', action='store_true')
    asyncio.run(main(parser.parse_args()))
