"""Regression controls for review findings F04/F05; no live server required."""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import venv
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'research/scripts'))
from check_cleanup_traces import project
from tests.cancellation.audit import validate_audit
from temporal_agent_harness.harness.agent_protocol.events import (
    AutoApprovalEvaluationEnded, AutoApprovalEvaluationError,
)


def records():
    with zipfile.ZipFile(ROOT / 'research/evaluation/cancellation-evidence/implementation.zip') as archive:
        return [json.loads(archive.read(n)) for n in archive.namelist()
                if n.endswith(('caller-second_raise.json', 'caller-second_return.json'))]


def test_explicit_and_default_driver_plans_keep_symlinked_venv(tmp_path):
    subject = tmp_path / 'subject'
    executable = subject / '.venv/bin/python'
    venv.EnvBuilder(with_pip=False, symlinks=True).create(subject / '.venv')
    assert executable.is_symlink()
    env = dict(os.environ)
    env.pop('PYTHONPATH', None)
    site = subprocess.check_output([str(executable), '-c',
        'import sysconfig; print(sysconfig.get_path("purelib"))'], text=True, env=env).strip()
    # A module installed only into this venv makes interpreter escape observable.
    (Path(site) / 'review_venv_dependency.py').write_text('VALUE = "venv-only"\n')
    outputs = []
    for extra in ([], ['--python', 'subject/.venv/bin/python']):
        plan = json.loads(subprocess.check_output([sys.executable,
            str(ROOT / 'research/scripts/reproduce_review.py'), '--subject', 'subject',
            '--stage', 'plan', *extra], cwd=tmp_path, text=True))
        for stage in ('cancellation', 'activity'):
            interpreter = plan['stages'][stage][0]['argv'][0]
            assert interpreter == str(executable)
            outputs.append(json.loads(subprocess.check_output([interpreter, '-c',
                'import sys,json,review_venv_dependency as d; print(json.dumps([sys.prefix,d.VALUE]))'],
                cwd=tmp_path, text=True, env=env)))
    assert outputs == [[str(subject / '.venv'), 'venv-only']] * 4


def test_retained_cancellation_records_pass():
    retained = records()
    assert len(retained) == 4
    for record in retained:
        assert len(project(record)) == 4


@pytest.mark.parametrize('mutation', ['tool', 'evaluation', 'ended', 'error'])
def test_corrupt_audit_is_rejected_before_projection(mutation):
    record = next(r for r in records() if r['variant'] == 'baseline')
    events = record['after']['events']
    terminal = next(e for e in events if e['type'] == 'auto_approval_evaluation_superseded')
    if mutation == 'tool':
        next(e for e in events if e['type'] == 'tool_start')['tool_id'] = 'unrelated-call'
    elif mutation == 'evaluation':
        terminal['evaluation_id'] = 'unrelated-evaluation'
    else:
        extra = deepcopy(terminal)
        if mutation == 'ended':
            extra.update(type='auto_approval_evaluation_ended', verdict='deny', reason=None, details={})
            extra = AutoApprovalEvaluationEnded.model_validate(extra).model_dump(mode='json')
        else:
            extra.pop('verdict', None)
            extra.update(type='auto_approval_evaluation_error', message='synthetic control')
            extra = AutoApprovalEvaluationError.model_validate(extra).model_dump(mode='json')
        events.append(extra)
    with pytest.raises(ValueError):
        project(record)
    with pytest.raises(ValueError):
        validate_audit(events)


def test_retained_fresh_activity_audits_pass():
    count = 0
    with zipfile.ZipFile(ROOT / 'research/evaluation/activity-evidence.zip') as archive:
        for name in archive.namelist():
            if name.startswith(('cases/baseline--', 'cases/corrected--', 'cases/versioned--')) and name.endswith('/result.json'):
                row = json.loads(archive.read(name))
                validate_audit(row['state']['events'])
                count += 1
    assert count == 12
