"""Measure regression sensitivity to isolated edits of the actual implementation.

Never edit the checkout under test. Each experiment copies the package and tests
into its own directory and runs a fresh interpreter. A mutant counts as detected
only when pytest reports assertion failures without collection/setup errors.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from check_model import ROOT

SOURCE = Path('temporal_agent_harness/harness/agent_workflow.py')
MUTATIONS = [
    ('denial_remember', 'if decision.approved and decision.remember and entry is not None:',
     'if decision.remember and entry is not None:', 'denied_remember'),
    ('scope_leak', 'if self._policy_auto_approves(\n                entry.tool_name, inherently_safe=entry.inherently_safe\n            ):',
     'if True:  # synthetic scope leak', 'different_tool'),
    ('reverse_publication', 'return [e for e in self._approvals.values() if e.status is _ApprovalStatus.PENDING]',
     'return list(reversed([e for e in self._approvals.values() if e.status is _ApprovalStatus.PENDING]))', 'policy_relax'),
]


def experiment(name, source, selector, should_fail):
    out = ROOT / 'research/results/implementation-mutations' / name
    if out.exists():
        shutil.rmtree(out)  # Only reproducible generated data in this named directory.
    out.mkdir(parents=True)
    for package in ('temporal_agent_harness', 'tests'):
        shutil.copytree(ROOT / package, out / package, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    (out / SOURCE).write_text(source)
    env = dict(os.environ, PYTHONPATH=str(out), PYTHONDONTWRITEBYTECODE='1')
    run = subprocess.run([sys.executable, '-m', 'pytest', 'tests/research/test_policy_cascade.py',
                          '-q', '-k', selector, '--junitxml=results.xml'],
                         cwd=out, env=env, capture_output=True, text=True, timeout=180)
    (out / 'pytest.log').write_text(run.stdout + run.stderr)
    if not (out / 'results.xml').exists():
        raise RuntimeError(f'{name}: no JUnit evidence; see {out}')
    suites = ET.parse(out / 'results.xml').getroot().findall('.//testsuite')
    counts = {key: sum(int(s.get(key, 0)) for s in suites) for key in ('tests', 'failures', 'errors', 'skipped')}
    valid = counts['tests'] == (6 if name == 'baseline' else 2) and counts['errors'] == counts['skipped'] == 0
    detected = run.returncode == 1 and counts['failures'] > 0
    ok = valid and (detected if should_fail else run.returncode == 0 and counts['failures'] == 0)
    if not ok:
        print((run.stdout + run.stderr)[-6000:])
        raise RuntimeError(f'{name}: invalid experiment outcome: {counts}, exit={run.returncode}')
    return dict(name=name, detected=detected, expected_failure=should_fail, returncode=run.returncode,
                implementation_sha256=hashlib.sha256(source.encode()).hexdigest(), **counts)


def main():
    original = (ROOT / SOURCE).read_text()
    results = [experiment('baseline', original, 'denied_remember or different_tool or policy_relax', False)]
    for name, before, after, selector in MUTATIONS:
        if original.count(before) != 1:
            raise SystemExit(f'{name}: mutation anchor drifted; review the experiment')
        results.append(experiment(name, original.replace(before, after), selector, True))
    summary = ROOT / 'research/results/implementation-mutations/summary.json'
    summary.write_text(json.dumps({'baseline_sha256': hashlib.sha256(original.encode()).hexdigest(),
                                   'results': results}, indent=2) + '\n')
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
