"""Run v4 fresh activities, cross-version replay, and live nonsticky replacements.

Only isolated copies receive corrections. Worker/replayer processes verify imports.
Every observation is retained before its acceptance assertion; failures keep prefixes.
"""
import argparse
import asyncio
from contextlib import asynccontextmanager
from datetime import timedelta
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

from prepare_cancellation_variant import corrected, SOURCE

ROOT = Path(__file__).resolve().parents[2]
PATCH_ID = 'approval-caller-cancel-v1'
SCENARIOS = ('approve', 'deny', 'second_raise', 'second_return')


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + '\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def history_projection(history):
    """Use server events, not observer tool-start messages, as command evidence."""
    events = json.loads(history.to_json())['events']
    def ids(kind):
        return [int(e['eventId']) for e in events if e['eventType'] == 'EVENT_TYPE_' + kind]
    return {'scheduled': ids('ACTIVITY_TASK_SCHEDULED'),
            'started': ids('ACTIVITY_TASK_STARTED'), 'completed': ids('ACTIVITY_TASK_COMPLETED'),
            'caller_signals': [int(e['eventId']) for e in events
                if e.get('workflowExecutionSignaledEventAttributes', {}).get('signalName') == 'cancel_caller'],
            'markers': [e['markerRecordedEventAttributes'] for e in events
                        if 'markerRecordedEventAttributes' in e],
            'nondeterministic_tasks': [int(e['eventId']) for e in events
                if e.get('workflowTaskFailedEventAttributes', {}).get('cause') ==
                'WORKFLOW_TASK_FAILED_CAUSE_NON_DETERMINISTIC_ERROR']}


def prepare(output):
    original = (ROOT / SOURCE).read_text()
    fixed = corrected(original)
    anchor = 'if caller is not None and caller.cancelling():'
    assert fixed.count(anchor) == 1
    versioned = fixed.replace(anchor, 'if caller is not None and caller.cancelling() and (\n'
        f'        not workflow.in_workflow() or workflow.patched("{PATCH_ID}")\n'
        '    ):')
    variants = {}
    for name, source in [('baseline', original), ('corrected', fixed), ('versioned', versioned)]:
        cwd = ROOT if name == 'baseline' else output / 'variants' / name
        if name != 'baseline':
            cwd.mkdir(parents=True)
            for folder in ('temporal_agent_harness', 'tests', 'examples'):
                shutil.copytree(ROOT / folder, cwd / folder,
                                ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            (cwd / SOURCE).write_text(source)
        manifest = {'variant': name, 'source_sha256': sha(cwd / SOURCE),
                    'probe_sha256': sha(cwd / 'tests/activity_upgrade/activity_probe.py'),
                    'cwd': str(cwd), 'patch_id': PATCH_ID if name == 'versioned' else None}
        manifest_path = output / (name + '-manifest.json')
        write(manifest_path, manifest)
        variants[name] = (cwd, manifest_path)
        if name != 'baseline':
            # A synchronous entry point lets pytest own its event loops. Imports
            # and bytes are checked before running the entire harness suite.
            (cwd / 'run_regressions.py').write_text('''from pathlib import Path
import hashlib, json, sys
import temporal_agent_harness.harness.agent_workflow as impl
expected = Path('temporal_agent_harness/harness/agent_workflow.py').resolve()
assert Path(impl.__file__).resolve() == expected, 'Wrong regression import'
manifest = json.loads(Path(sys.argv[1]).read_text())
assert hashlib.sha256(expected.read_bytes()).hexdigest() == manifest['source_sha256']
import pytest
sys.exit(pytest.main(['tests/harness/', '-q', '--junitxml=' + sys.argv[2]]))
''')
    # Retain exact proposed implementation diffs, not only their fingerprints.
    import difflib
    for name, source in [('corrected', fixed), ('versioned', versioned)]:
        (output / (name + '.patch')).write_text(''.join(difflib.unified_diff(
            original.splitlines(True), source.splitlines(True),
            fromfile='a/' + str(SOURCE), tofile='b/' + str(SOURCE))))
    return variants


class Study:
    def __init__(self, output, variants):
        self.output, self.variants = output, variants
        self.fresh, self.live, self.errors = [], [], []
        self.client = None

    def ledger(self, case):
        path = self.output / 'cases' / case / 'ledger.jsonl'
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    @asynccontextmanager
    async def worker(self, variant, queue, case, phase):
        directory = self.output / 'cases' / case
        directory.mkdir(parents=True, exist_ok=True)
        ready, stop = directory / (phase + '.ready.json'), directory / (phase + '.stop')
        cwd, manifest = self.variants[variant]
        log = open(directory / (phase + '.log'), 'w')
        process = await asyncio.create_subprocess_exec(
            sys.executable, str(ROOT / 'research/scripts/activity_process.py'), 'worker',
            '--manifest', str(manifest), '--address', self.client.service_client.config.target_host,
            '--queue', queue, '--ledger', str(directory / 'ledger.jsonl'),
            '--ready', str(ready), '--stop', str(stop), cwd=cwd, stdout=log, stderr=log,
            env={**os.environ, 'PYTHONPATH': str(cwd)})
        try:
            async with asyncio.timeout(30):
                while not ready.exists():
                    if process.returncode is not None:
                        raise RuntimeError(f'Worker {phase} exited {process.returncode}; inspect retained log')
                    await asyncio.sleep(0.05)
            yield
        finally:
            stop.touch()
            try:
                async with asyncio.timeout(20):
                    code = await process.wait()
                if code:
                    raise RuntimeError(f'Worker {phase} exited {code}')
            except TimeoutError:
                process.kill()
                await process.wait()
                raise
            finally:
                log.close()

    async def observe(self, handle, case, label):
        history = await handle.fetch_history()
        directory = self.output / 'cases' / case
        directory.mkdir(parents=True, exist_ok=True)
        (directory / (label + '.history.json')).write_text(history.to_json())
        return history_projection(history)

    async def until(self, handle, case, label, predicate, allow_nondeterminism=False):
        from temporalio.service import RPCError
        async with asyncio.timeout(40):
            while True:
                projection = await self.observe(handle, case, label)
                if allow_nondeterminism and projection['nondeterministic_tasks']:
                    return {'recovery': 'nondeterministic', 'history': projection}
                try:
                    state = await handle.query('evidence', rpc_timeout=timedelta(seconds=2))
                    write(self.output / 'cases' / case / (label + '.json'), state)
                    if predicate(state):
                        return {'recovery': 'compatible', 'state': state, 'history': projection}
                except RPCError as exc:
                    # A query timeout is never scored as nondeterminism. Only the
                    # explicit server event above can establish that conclusion.
                    write(self.output / 'cases' / case / (label + '-query-error.json'), {'error': repr(exc)})
                await asyncio.sleep(0.05)

    async def start(self, queue, case, mode):
        from temporal_agent_harness.harness.agent_protocol import AgentConfig, AgentMessage
        handle = await self.client.start_workflow('ActivityAgent', AgentConfig(),
            id='activity-' + uuid.uuid4().hex, task_queue=queue)
        await handle.execute_update('send_agent_message', AgentMessage(type='act', payload={'text': mode + ':' + case}))
        await self.until(handle, case, 'started', lambda s: s['started'])
        return handle

    async def approve(self, handle, approved=True):
        from temporal_agent_harness.harness.agent_protocol import ToolApprovalDecision
        await handle.execute_update('tool_approval', ToolApprovalDecision(tool_id='call', approved=approved))

    async def close(self, handle):
        await handle.signal('close')
        async with asyncio.timeout(30):
            await handle.result()

    async def run_fresh(self, variant, scenario):
        case = variant + '--' + scenario
        queue = 'activity-' + uuid.uuid4().hex
        async with self.worker(variant, queue, case, 'worker'):
            handle = await self.start(queue, case, scenario)
            await self.approve(handle, scenario != 'deny')
            if scenario.startswith('second_'):
                await self.until(handle, case, 'before-cancel', lambda s: s['cleanup_entered'])
                await handle.signal('cancel_caller')
            observed = await self.until(handle, case, 'finished', lambda s: s['outcome'] is not None)
            await self.close(handle)
            history = await handle.fetch_history()
            (self.output / 'histories' / (case + '.history.json')).write_text(history.to_json())
            row = {'case': case, 'variant': variant, 'scenario': scenario,
                   'state': observed['state'], 'history': history_projection(history),
                   'ledger': self.ledger(case)}
            self.fresh.append(row)
            write(self.output / 'cases' / case / 'result.json', row)
            expected = ('rejected' if scenario == 'deny' else 'cancelled'
                        if scenario.startswith('second_') and variant != 'baseline' else 'dispatched')
            assert row['state']['outcome'] == expected
            assert row['state']['status'] == ('denied' if scenario == 'deny' else 'approved')
            count = int(expected == 'dispatched')
            assert len(row['ledger']) == len(row['history']['scheduled']) == len(row['history']['completed']) == count
            assert all(e['workflow_id'] == handle.id and e['attempt'] == 1 for e in row['ledger'])
            terminals = [e for e in row['state']['events']
                         if e['type'] == 'auto_approval_evaluation_superseded']
            assert len(terminals) == 1
            if scenario.startswith('second_'):
                assert row['state']['caller_cancel_requested'] and row['state']['second_cancel']
                assert len(row['history']['caller_signals']) == 1
                if count:
                    assert row['history']['caller_signals'][0] < row['history']['scheduled'][0]

    async def run_live(self, target, mode, cut):
        case = f'live--{target}--{mode}--{cut}'
        queue = 'activity-' + uuid.uuid4().hex
        async with self.worker('baseline', queue, case, 'old'):
            handle = await self.start(queue, case, mode)
            await self.approve(handle)
            before = await self.until(handle, case, 'old-cleanup', lambda s: s['cleanup_entered'])
            if cut == 'after_activity':
                await handle.signal('cancel_caller')
                before = await self.until(handle, case, 'old-completed', lambda s: s['outcome'] == 'dispatched')
            before_ledger = self.ledger(case)
            await self.observe(handle, case, 'replacement-prefix')
        async with self.worker(target, queue, case, 'new'):
            await handle.signal('checkpoint')
            recovered = await self.until(handle, case, 'recovered', lambda s: s['checkpoints'] >= 1,
                                         allow_nondeterminism=True)
            if recovered['recovery'] == 'compatible' and cut == 'before_cancel':
                assert recovered['state']['status'] == 'approved'
                assert recovered['state']['outcome'] is None
                await handle.signal('cancel_caller')
                recovered = await self.until(handle, case, 'new-cancelled', lambda s: s['outcome'] is not None,
                                             allow_nondeterminism=True)
            row = {'case': case, 'target': target, 'mode': mode, 'cut': cut,
                   'before': before, 'recovered': recovered,
                   'ledger_before': before_ledger, 'ledger_after': self.ledger(case)}
            self.live.append(row)
            write(self.output / 'cases' / case / 'result.json', row)
            if recovered['recovery'] == 'compatible':
                await self.close(handle)
            else:
                # Preserve the explicit failed-task history before administrative
                # teardown; termination is cleanup, not an experimental outcome.
                await handle.terminate(reason='v4 experiment finished after recorded nondeterminism')
            row['terminal_history'] = await self.observe(handle, case, 'terminal')
            row['ledger_after'] = self.ledger(case)
            write(self.output / 'cases' / case / 'result.json', row)
            if cut == 'before_cancel':
                assert recovered['recovery'] == 'compatible'
                assert recovered['state']['outcome'] == 'cancelled'
                assert not row['ledger_after'] and not row['terminal_history']['scheduled']
            elif target == 'versioned':
                assert recovered['recovery'] == 'compatible'
                assert recovered['state']['outcome'] == 'dispatched'
                assert len(row['ledger_before']) == len(row['ledger_after']) == 1
                assert len(row['terminal_history']['scheduled']) == 1
            # The unversioned post-activity case is measured, not pre-scored.

    async def replay(self):
        for name, (cwd, manifest) in self.variants.items():
            with open(self.output / (name + '-replay.log'), 'w') as log:
                process = await asyncio.create_subprocess_exec(sys.executable,
                    str(ROOT / 'research/scripts/activity_process.py'), 'replay',
                    '--manifest', str(manifest), '--histories', str(self.output / 'histories'),
                    '--result', str(self.output / (name + '-replay.json')),
                    cwd=cwd, stdout=log, stderr=log, env={**os.environ, 'PYTHONPATH': str(cwd)})
                async with asyncio.timeout(420):
                    code = await process.wait()
                assert code == 0, f'{name} replay failed; inspect retained log'
        versioned = json.loads((self.output / 'versioned-replay.json').read_text())
        assert all(r['command'] == 'compatible' for r in versioned['rows']
                   if r['history'].startswith('baseline--')), 'Versioned remedy failed baseline replay'

    async def run(self):
        from temporalio.testing import WorkflowEnvironment
        from temporalio.contrib.pydantic import pydantic_data_converter
        try:
            async with await WorkflowEnvironment.start_time_skipping(data_converter=pydantic_data_converter) as env:
                self.client = env.client
                for variant in self.variants:
                    for scenario in SCENARIOS:
                        await self.run_fresh(variant, scenario)
                await self.replay()
                for target in ('corrected', 'versioned'):
                    for mode in ('second_raise', 'second_return'):
                        for cut in ('before_cancel', 'after_activity'):
                            await self.run_live(target, mode, cut)
        except BaseException as exc:
            self.errors.append({'type': type(exc).__name__, 'error': repr(exc)})
            raise
        finally:
            write(self.output / 'summary.json', {'schema': 1, 'fresh': self.fresh,
                'live': self.live, 'errors': self.errors,
                'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                'runner_sha256': sha(Path(__file__)),
                'process_sha256': sha(ROOT / 'research/scripts/activity_process.py'),
                'lock_sha256': sha(ROOT / 'uv.lock')})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'research/results/activity-upgrade')
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)  # Never mix a failed prefix into a rerun.
    (output / 'histories').mkdir()
    sys.path.insert(0, str(ROOT))
    asyncio.run(Study(output, prepare(output)).run())
