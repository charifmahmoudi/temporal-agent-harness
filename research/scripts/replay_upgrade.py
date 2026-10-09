"""Replay the frozen v2 histories and measure command and application agreement.

Run once from each provenance-checked source directory. This does not start a
server or execute an external tool effect; the retained probe is workflow-local.
"""
import argparse
import asyncio
import copy
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import sys
import time
import zipfile

ARCHIVE_SHA = '13da869cfd18ab1e0ecb03a2e7c39290a0e519da870f4e07205be18377b842b7'
WORKFLOW_SHA = 'a572fbcd079464a5647c8fe4a397c5bee832dd77a0b0b7ea767ddd17a4183560'
LOCK_SHA = '2f579bed101ee2d63d0f77e1d979188115a1b549a3b4aacb6adcb96646d4a1b2'
SOURCE = Path('temporal_agent_harness/harness/agent_workflow.py')
WORKFLOW = Path('tests/cancellation/test_cancellation_recovery.py')
PREFIXES = {
    'baseline': 'cancellation/baseline/',
    'corrected': 'cancellation-corrected/research/results/cancellation/corrected/',
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def projection(evidence):
    """Compare application obligations, excluding timing and generated event IDs."""
    events = evidence['events']
    return {
        'status': evidence['status'],
        'outcome': evidence['outcome'],
        'tool_starts': sum(e['type'] == 'tool_start' for e in events),
        'evaluation_terminals': sum(
            e['type'].startswith('auto_approval_evaluation_')
            and e['type'] != 'auto_approval_evaluation_started' for e in events),
    }


def original_projection(archive, prefix, scenario):
    # The workflow-cancel record has no final application observation. Its
    # pre-cancel snapshot cannot serve as a post-cancel semantic oracle.
    if scenario == 'workflow-cancel':
        return None
    name = ('released-' + scenario.removeprefix('delayed-')
            if scenario.startswith('delayed-') else
            'restart-after' if scenario == 'restart' else scenario)
    evidence = json.loads(archive.read(prefix + name + '.json'))
    return projection(evidence['after'] if scenario.startswith('caller-') else evidence)


def comparison(expected, actual):
    if expected is None:
        return 'unavailable'
    if actual is None:
        return 'missing_observation'
    return 'match' if expected == actual else 'mismatch'


def command_result(failure):
    from temporalio.workflow import NondeterminismError
    return ('compatible' if failure is None else 'nondeterministic'
            if isinstance(failure, NondeterminismError) else 'experiment_error')


async def measure(args):
    # Cwd, not the editable original install, must determine the tested source.
    cwd = Path.cwd().resolve()
    sys.path.insert(0, str(cwd))
    sys.path.insert(0, str(cwd / WORKFLOW.parent))
    import temporal_agent_harness.harness.agent_workflow as implementation
    import test_cancellation_recovery as probe
    from temporalio import workflow
    from temporalio.client import WorkflowHistory
    from temporalio.contrib.pydantic import pydantic_data_converter
    from temporalio.worker import Interceptor, Replayer, UnsandboxedWorkflowRunner, WorkflowInboundInterceptor

    snapshot = json.loads((args.root / 'research/evaluation/cancellation-results.json').read_text())
    source_hash = digest((cwd / SOURCE).read_bytes())
    if Path(implementation.__file__).resolve() != cwd / SOURCE:
        raise RuntimeError('Wrong implementation import path')
    if source_hash != snapshot['source_hashes'][args.variant + '_sha256']:
        raise RuntimeError('Source differs from the frozen variant')
    if Path(probe.__file__).resolve() != cwd / WORKFLOW:
        raise RuntimeError('Wrong workflow import path')
    if digest((cwd / WORKFLOW).read_bytes()) != WORKFLOW_SHA:
        raise RuntimeError('Experiment workflow differs from the frozen definition')
    if digest((args.root / 'uv.lock').read_bytes()) != LOCK_SHA:
        raise RuntimeError('Dependency lock differs from the frozen experiment')
    archive_path = args.root / 'research/evaluation/cancellation-evidence/implementation.zip'
    if digest(archive_path.read_bytes()) != ARCHIVE_SHA:
        raise RuntimeError('Frozen input archive changed')

    rows = []
    with zipfile.ZipFile(archive_path) as archive:
        for origin, prefix in PREFIXES.items():
            histories = sorted(n for n in archive.namelist()
                               if n.startswith(prefix) and n.endswith('.history.json'))
            if len(histories) != 16:
                raise RuntimeError('Incomplete or duplicated history inventory')
            for name in histories:
                scenario = name.removeprefix(prefix).removesuffix('.history.json')
                expected = original_projection(archive, prefix, scenario)
                observations = []

                class TerminalObserver(WorkflowInboundInterceptor):
                    async def execute_workflow(self, input):
                        try:
                            return await super().execute_workflow(input)
                        finally:
                            # A synchronous read-only copy; no command or await
                            # is added to the original workflow's execution.
                            observations.append(copy.deepcopy(workflow.instance().evidence()))

                class Observe(Interceptor):
                    def workflow_interceptor_class(self, input):
                        return TerminalObserver

                raw = archive.read(name)
                row = {'origin': origin, 'target': args.variant, 'scenario': scenario,
                       'history_sha256': digest(raw), 'expected': expected}
                started = time.monotonic()
                try:
                    history = WorkflowHistory.from_json(scenario, raw.decode())
                    async with asyncio.timeout(30):
                        result = await Replayer(
                            workflows=[probe.CleanupAgent],
                            workflow_runner=UnsandboxedWorkflowRunner(),
                            data_converter=pydantic_data_converter,
                            interceptors=[Observe()],
                        ).replay_workflow(history, raise_on_replay_failure=False)
                    failure = result.replay_failure
                    row['command'] = command_result(failure)
                    row['error'] = repr(failure) if failure else None
                    # Paired ablation: the same bytes without the observer must
                    # have the same command result. This cannot prove complete
                    # noninterference, but exposes changed replay classification.
                    async with asyncio.timeout(30):
                        plain = await Replayer(
                            workflows=[probe.CleanupAgent],
                            workflow_runner=UnsandboxedWorkflowRunner(),
                            data_converter=pydantic_data_converter,
                        ).replay_workflow(history, raise_on_replay_failure=False)
                    row['unobserved_command'] = command_result(plain.replay_failure)
                    row['unobserved_error'] = repr(plain.replay_failure) if plain.replay_failure else None
                except Exception as exc:
                    row.update(command='experiment_error', error=repr(exc))
                row['seconds'] = time.monotonic() - started
                row['observations'] = observations
                row['actual'] = projection(observations[-1]) if observations else None
                row['application'] = (comparison(expected, row['actual'])
                                      if row['command'] == 'compatible' else 'not_scored')
                rows.append(row)
                print(f"{origin} -> {args.variant}: {scenario}: {row['command']}, {row['application']}", flush=True)

    # Reject an invalid expected outcome through exactly the same comparator.
    control = next(r for r in rows if r['origin'] == args.variant and r['scenario'] == 'approve-propagate')
    altered = dict(control['expected'], outcome='cancelled')
    negative_control = comparison(altered, control['actual']) == 'mismatch'
    report = {'schema': 1, 'variant': args.variant, 'archive_sha256': ARCHIVE_SHA,
              'source_sha256': source_hash, 'workflow_sha256': digest((cwd / WORKFLOW).read_bytes()),
              'runner_sha256': digest(Path(__file__).read_bytes()),
              'lock_sha256': digest((args.root / 'uv.lock').read_bytes()),
              'python': platform.python_version(), 'temporalio': importlib.metadata.version('temporalio'),
              'negative_control_rejected': negative_control, 'rows': rows}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    failures = [r for r in rows if r['command'] == 'experiment_error'
                or r.get('unobserved_command') != r['command']
                or r['application'] == 'missing_observation'
                or (r['origin'] == args.variant and
                    (r['command'] != 'compatible' or r['application'] not in {'match', 'unavailable'}))]
    if failures or not negative_control:
        raise SystemExit('Invalid experiment or same-version control; inspect retained output')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True, help='Original repository root')
    parser.add_argument('--variant', choices=PREFIXES, required=True)
    parser.add_argument('--output', type=Path, required=True)
    asyncio.run(measure(parser.parse_args()))
