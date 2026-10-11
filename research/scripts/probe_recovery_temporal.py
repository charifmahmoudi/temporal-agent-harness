"""CI-only exploratory recovery operations, not a product defect oracle."""
import asyncio
from datetime import timedelta
import hashlib
import json
import os
from pathlib import Path
import traceback

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.worker import Worker

OUT = Path('research/results/discovery-recovery/temporal')


@activity.defn
async def record_effect(data: dict) -> str:
    with (OUT / 'ledger.jsonl').open('a') as f:
        f.write(json.dumps(data) + '\n')
    return data['kind']


@workflow.defn(name='DiscoveryRecovery', sandboxed=False)
class Original:
    @workflow.run
    async def run(self, key: str):
        await workflow.execute_activity(record_effect, {'key': key, 'kind': 'effect'},
                                        start_to_close_timeout=timedelta(seconds=10))
        try:
            await workflow.wait_condition(lambda: False)
        except asyncio.CancelledError:
            await workflow.execute_activity(record_effect, {'key': key, 'kind': 'cleanup'},
                                            start_to_close_timeout=timedelta(seconds=10))
            raise

    @workflow.signal
    async def wake(self):
        pass


@workflow.defn(name='DiscoveryRecovery', sandboxed=False)
class Broken:
    @workflow.run
    async def run(self, key: str):
        await workflow.sleep(timedelta(days=1))

    @workflow.signal
    async def wake(self):
        pass


async def poll(fn, predicate, seconds=60):
    deadline = asyncio.get_running_loop().time() + seconds
    while True:
        value = await fn()
        if predicate(value):
            return value
        if asyncio.get_running_loop().time() >= deadline:
            raise TimeoutError(repr(value))
        await asyncio.sleep(.25)


def ledger(key):
    p = OUT / 'ledger.jsonl'
    return [json.loads(line) for line in p.read_text().splitlines()
            if json.loads(line)['key'] == key] if p.exists() else []


async def trial(client, repetition, arm):
    key = f'discovery-{repetition}-{arm}'
    row = {'key': key, 'arm': arm, 'repetition': repetition, 'error': None}
    handle = None
    async def history():
        h = await handle.fetch_history()
        obj = json.loads(h.to_json())
        (OUT / f'{key}-history.json').write_text(json.dumps(obj, indent=2))
        return obj['events']
    async def status():
        return (await handle.describe()).status.name
    def worker(cls):
        return Worker(client, task_queue=key, workflows=[cls], activities=[record_effect],
                      max_cached_workflows=0)
    try:
        async with worker(Original):
            handle = await client.start_workflow('DiscoveryRecovery', key, id=key, task_queue=key)
            row['barrier'] = await poll(history, lambda es: any('activityTaskCompletedEventAttributes' in e for e in es)
                and es[-1].get('eventType') == 'EVENT_TYPE_WORKFLOW_TASK_COMPLETED')
        async with worker(Original if arm == 'compatible_cancel' else Broken):
            await handle.signal('wake')
            if arm != 'compatible_cancel':
                es = await poll(history, lambda es: any(e.get('workflowTaskFailedEventAttributes', {}).get('cause')
                      == 'WORKFLOW_TASK_FAILED_CAUSE_NON_DETERMINISTIC_ERROR' for e in es))
                row['mismatch_events'] = [e for e in es if e.get('workflowTaskFailedEventAttributes', {}).get('cause')
                                         == 'WORKFLOW_TASK_FAILED_CAUSE_NON_DETERMINISTIC_ERROR']
            if arm == 'broken_force':
                await handle.terminate('exploratory recovery probe')
                row['acknowledged'] = True
                row['terminal'] = await poll(status, lambda s: s != 'RUNNING')
            else:
                await handle.cancel()
                row['acknowledged'] = True
                if arm == 'compatible_cancel':
                    row['terminal'] = await poll(status, lambda s: s != 'RUNNING')
                else:
                    await asyncio.sleep(12)
                    row['before_restore'] = {'status': await status(), 'ledger': ledger(key)}
                    await history()
        if arm == 'broken_cancel_restore':
            async with worker(Original):
                row['terminal'] = await poll(status, lambda s: s != 'RUNNING')
        row['ledger'] = ledger(key)
        await history()
        row['cleanup_count'] = sum(e['kind'] == 'cleanup' for e in row['ledger'])
        row['effect_count'] = sum(e['kind'] == 'effect' for e in row['ledger'])
        row['matches_prediction'] = row['effect_count'] == 1 and (
            row['terminal'] == 'TERMINATED' and row['cleanup_count'] == 0 if arm == 'broken_force'
            else row['terminal'] == 'CANCELED' and row['cleanup_count'] == 1)
        if arm == 'broken_cancel_restore':
            row['matches_prediction'] &= row['before_restore']['status'] == 'RUNNING' and not any(
                e['kind'] == 'cleanup' for e in row['before_restore']['ledger'])
    except Exception as exc:
        row['error'] = {'type': type(exc).__name__, 'message': str(exc), 'traceback': traceback.format_exc()}
        if handle:
            try:
                await history()
                await handle.terminate('inconclusive trial cleanup')
            except Exception:
                pass
    # Histories are separate raw artifacts; summaries preserve decisive events only.
    row.pop('barrier', None)
    return row


async def main():
    if os.environ.get('GITHUB_ACTIONS') != 'true':
        raise SystemExit('Run only in GitHub Actions')
    OUT.mkdir(parents=True, exist_ok=True)
    client = await Client.connect('localhost:7233')
    report = {'engine': 'temporal', 'protocol': 1, 'commit': os.environ['GITHUB_SHA'],
              'run': os.environ['GITHUB_RUN_ID'], 'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'cases': []}
    for repetition in range(3):
        for arm in ('compatible_cancel', 'broken_cancel_restore', 'broken_force'):
            row = await trial(client, repetition, arm)
            report['cases'].append(row)
            (OUT / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
            print('RECOVERY_CASE=' + json.dumps(row), flush=True)
    print('RECOVERY_PROBE_JSON=' + json.dumps(report), flush=True)
    if any(r['error'] or not r.get('matches_prediction') for r in report['cases']):
        raise SystemExit('Incomplete or prediction differs; inspect evidence')


if __name__ == '__main__':
    asyncio.run(main())
