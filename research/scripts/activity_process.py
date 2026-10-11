"""Isolated worker/replayer process; verify imported source before touching histories."""
import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import platform
import sys


async def main(args):
    cwd = Path.cwd().resolve()
    sys.path.insert(0, str(cwd))
    sys.path.insert(0, str(cwd / 'tests/activity_upgrade'))
    import temporal_agent_harness.harness.agent_workflow as implementation
    import activity_probe as probe
    from temporalio import workflow
    from temporalio.client import Client, WorkflowHistory
    from temporalio.contrib.pydantic import pydantic_data_converter
    from temporalio.worker import Replayer, UnsandboxedWorkflowRunner, Worker
    from temporal_agent_harness.harness import agent
    from replay_upgrade import command_result

    manifest = json.loads(args.manifest.read_text())
    source = cwd / 'temporal_agent_harness/harness/agent_workflow.py'
    assert Path(implementation.__file__).resolve() == source, 'Wrong source import'
    assert hashlib.sha256(source.read_bytes()).hexdigest() == manifest['source_sha256']
    assert Path(probe.__file__).resolve() == cwd / 'tests/activity_upgrade/activity_probe.py'
    assert hashlib.sha256(Path(probe.__file__).read_bytes()).hexdigest() == manifest['probe_sha256']
    os.environ['ACTIVITY_SOURCE_SHA'] = manifest['source_sha256']
    if args.mode == 'worker':
        os.environ['ACTIVITY_LEDGER'] = str(args.ledger)
        client = await Client.connect(args.address, data_converter=pydantic_data_converter)
        async with Worker(client, task_queue=args.queue, workflows=[probe.ActivityAgent],
                          activities=[agent.tool_activity(probe.ledger_probe)],
                          workflow_runner=UnsandboxedWorkflowRunner(), max_cached_workflows=0):
            args.ready.write_text(json.dumps(manifest))
            while not args.stop.exists():
                await asyncio.sleep(0.05)
    else:
        rows = []
        for path in sorted(args.histories.glob('*.history.json')):
            raw = path.read_bytes()
            row = {'history': path.name, 'target': manifest['variant'],
                   'history_sha256': hashlib.sha256(raw).hexdigest()}
            try:
                history = WorkflowHistory.from_json(path.stem, raw.decode())
                async with asyncio.timeout(30):
                    result = await Replayer(workflows=[probe.ActivityAgent],
                        workflow_runner=UnsandboxedWorkflowRunner(),
                        data_converter=pydantic_data_converter).replay_workflow(
                            history, raise_on_replay_failure=False)
                row.update(command=command_result(result.replay_failure),
                           error=repr(result.replay_failure) if result.replay_failure else None)
            except Exception as exc:
                row.update(command='experiment_error', error=repr(exc))
            rows.append(row)
        args.result.write_text(json.dumps({'manifest': manifest, 'python': platform.python_version(),
                                          'rows': rows}, indent=2) + '\n')
        assert len(rows) == 12, 'Missing planned fresh histories'
        assert all(r['command'] != 'experiment_error' for r in rows)
        assert all(r['command'] == 'compatible' for r in rows
                   if r['history'].startswith(manifest['variant'] + '--'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['worker', 'replay'])
    parser.add_argument('--manifest', type=Path, required=True)
    for field in ('ready', 'stop', 'ledger', 'histories', 'result'):
        parser.add_argument('--' + field, type=Path)
    parser.add_argument('--address')
    parser.add_argument('--queue')
    asyncio.run(main(parser.parse_args()))
