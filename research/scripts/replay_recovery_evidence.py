"""Replay the identical retained histories offline; no test server is required."""
import asyncio
import base64
import gzip
import hashlib
import json
import platform
from importlib.metadata import version
from pathlib import Path
import sys

from temporalio.client import WorkflowHistory
from temporalio.worker import Replayer, UnsandboxedWorkflowRunner
from reproduce_recovery_673 import RecoveryBoundaryProbe, classify


async def main():
    source = Path(__file__).resolve().parents[1] / 'evaluation/recovery-673-evidence.json'
    bundle = json.loads(source.read_text())
    rows = []
    for arm in bundle['arms']:
        for item, case in zip(arm['histories'], arm['summary']['cases'], strict=True):
            raw = gzip.decompress(base64.b64decode(item['gzip_base64']))
            assert hashlib.sha256(raw).hexdigest() == item['sha256'] == case['history_sha256']
            assert case['resumed'] is True and case['finished'] == 2
            failure = None
            try:
                await Replayer(workflows=[RecoveryBoundaryProbe],
                    workflow_runner=UnsandboxedWorkflowRunner()).replay_workflow(
                        WorkflowHistory.from_json(item['name'], raw.decode()))
            except Exception as exc:
                failure = exc
            rows.append({'producer_sdk': arm['summary']['sdk_version'],
                'history': item['name'], 'history_sha256': item['sha256'],
                'verdict': classify(True, failure),
                'exception_type': type(failure).__name__ if failure else None,
                'exception': str(failure) if failure else None})
    report = {'python': platform.python_version(), 'sandbox': False,
        'dependencies': {name: version(name) for name in
            ('temporalio', 'protobuf', 'typing-extensions', 'types-protobuf')},
        'evidence_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'cases': rows}
    Path(sys.argv[1]).write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'sdk': version('temporalio'), 'verdicts': [r['verdict'] for r in rows]}))


if __name__ == '__main__':
    asyncio.run(main())
