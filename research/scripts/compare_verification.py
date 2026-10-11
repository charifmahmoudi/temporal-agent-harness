"""Execute the frozen exploratory comparison without rewarding experiment errors.

Production source and assertion-based suites are copied verbatim. Only collector
copies lose assertions, so bad observations can reach the independent TLC oracle.
The corpus deliberately includes an excluded malformed-input fault.
"""
import argparse
import ast
from contextlib import redirect_stdout
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

import check_cascade_traces as cascade
import check_traces as approval
from check_model import ROOT, JAR_SHA256

RESULTS = ROOT / 'research/results/comparison'
EXISTING = ['tests/harness/test_tool_approvals.py']
EXPANDED = EXISTING + ['tests/harness/test_auto_mode_superseded_result.py', 'tests/research/']


def digest(data):
    return hashlib.sha256(data).hexdigest()


class Collector(ast.NodeTransformer):
    """Drop behavioral assertions, preserving all workflow and stimulus statements."""
    def visit_Assert(self, node):
        if any(isinstance(n, ast.Await) for n in ast.walk(node)):
            raise ValueError('Assertion contains a scheduling operation; review required')
        return ast.copy_location(ast.Pass(), node)


def prepare(name, arm, source, collect=False):
    out = RESULTS / name / arm
    out.mkdir(parents=True)
    for folder in ('temporal_agent_harness', 'tests', 'research/models'):
        shutil.copytree(ROOT / folder, out / folder,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc', 'states'))
    shutil.copy(ROOT / 'pyproject.toml', out / 'pyproject.toml')
    source_path = out / 'temporal_agent_harness/harness/agent_workflow.py'
    source_path.write_text(source)
    transformations = {}
    if collect:
        for name in ('test_approval_traces.py', 'test_policy_cascade.py'):
            path = out / 'tests/research' / name
            tree = Collector().visit(ast.parse(path.read_text()))
            transformed = ast.unparse(ast.fix_missing_locations(tree)) + '\n'
            path.write_text(transformed)
            transformations[name] = digest(transformed.encode())
    (out / 'provenance.json').write_text(json.dumps({
        'source_sha256': digest(source.encode()), 'collector_sha256': transformations}, indent=2)+'\n')
    return out


def pytest_run(out, files, selector=None):
    # Raise explicitly: provenance must not depend on the collector's assertions.
    bootstrap = (
        "from pathlib import Path; import temporal_agent_harness.harness.agent_workflow as impl; "
        "expected=Path('temporal_agent_harness/harness/agent_workflow.py').resolve(); "
        "actual=Path(impl.__file__).resolve(); "
        "exec('if actual != expected: raise RuntimeError(str(actual))'); "
        "import pytest, sys; sys.exit(pytest.main(sys.argv[1:]))")
    args = [sys.executable, '-c', bootstrap, *files, '-q', '-x', '--junitxml=results.xml']
    if selector:
        args += ['-k', selector]
    start = time.monotonic()
    try:
        run = subprocess.run(args, cwd=out, capture_output=True, text=True, timeout=240,
                             env=dict(os.environ, PYTHONPATH=str(out), PYTHONDONTWRITEBYTECODE='1'))
        log, code = run.stdout + run.stderr, run.returncode
    except subprocess.TimeoutExpired as exc:
        log = (exc.stdout or b'').decode(errors='replace') if isinstance(exc.stdout, bytes) else (exc.stdout or '')
        (out / 'pytest.log').write_text(log)
        return {'outcome': 'inconclusive', 'reason': 'timeout', 'seconds': time.monotonic()-start}
    (out / 'pytest.log').write_text(log)
    xml = out / 'results.xml'
    if not xml.exists():
        return {'outcome': 'inconclusive', 'reason': 'missing JUnit', 'returncode': code,
                'seconds': time.monotonic()-start}
    suites = ET.parse(xml).getroot().findall('.//testsuite')
    counts = {k: sum(int(s.get(k, 0)) for s in suites) for k in ('tests', 'failures', 'errors', 'skipped')}
    failures = [f for case in ET.parse(xml).getroot().iter('testcase') for f in case.findall('failure')]
    assertion = any('AssertionError' in (f.get('message', '') + (f.text or '')) for f in failures)
    valid = counts['tests'] > 0 and counts['errors'] == counts['skipped'] == 0
    if valid and code == 0 and not counts['failures']:
        outcome = 'survived'
    elif valid and code == 1 and counts['failures'] and assertion:
        outcome = 'detected'
    else:
        outcome = 'inconclusive'
    return {'outcome': outcome, 'returncode': code, **counts,
            'seconds': time.monotonic()-start}


def trace_arm(source, fault, jar):
    model = fault['trace_model']
    if model is None:
        return {'outcome': 'out_of_scope', 'reason': 'Malformed input excluded from model'}
    out = prepare(fault['id'], 'trace', source, collect=True)
    file = 'test_policy_cascade.py' if model == 'cascade' else 'test_approval_traces.py'
    collected = pytest_run(out, ['tests/research/'+file], fault['trace_selector'])
    expected = 2 if model == 'cascade' else 1
    if collected['outcome'] != 'survived' or collected.get('tests') != expected:
        return {'outcome': 'inconclusive', 'reason': 'collector did not complete fixed stimuli',
                'collector': collected, 'seconds': collected['seconds']}
    folder = 'cascade-traces' if model == 'cascade' else 'traces'
    paths = sorted((out / 'research/results' / folder).glob('*.json'))
    if len(paths) != expected:
        return {'outcome': 'inconclusive', 'reason': 'missing traces', 'collector': collected}
    checker = cascade if model == 'cascade' else approval
    checker.ROOT = out  # Every generated model, witness, and log stays in this arm.
    start = time.monotonic()
    details = []
    for path in paths:
        trace = json.loads(path.read_text())
        if trace.get('schema') != 2 or trace.get('implementation_sha256') != digest(source.encode()):
            details.append({'trace': path.name, 'outcome': 'inconclusive', 'reason': 'stale/schema mismatch'})
            continue
        name = path.stem
        try:
            with (out / (name+'-checker.log')).open('w') as diagnostic, redirect_stdout(diagnostic):
                if model == 'cascade':
                    checker.check(jar, trace['observations'], name, trace['different_tools'], True,
                                  trace['registration_order'])
                else:
                    checker.check(jar, trace['observations'], name, True)
            outcome = 'matched'
        except (RuntimeError, ValueError, KeyError, subprocess.TimeoutExpired) as exc:
            logpath = out / 'research/results' / ('cascade-conformance' if model == 'cascade' else 'conformance') / name / 'TLC.log'
            log = logpath.read_text() if logpath.exists() else ''
            exhausted = ('unexpected TLC result 0;' in str(exc) and
                         'Model checking completed. No error has been found.' in log)
            outcome = 'rejected' if exhausted else 'inconclusive'
        details.append({'trace': path.name, 'outcome': outcome})
    checker.ROOT = ROOT
    if any(d['outcome'] == 'rejected' for d in details):
        outcome = 'detected'
    elif any(d['outcome'] == 'inconclusive' for d in details):
        outcome = 'inconclusive'
    else:
        outcome = 'survived'
    return {'outcome': outcome, 'traces': details, 'collector': collected,
            'seconds': collected['seconds']+time.monotonic()-start}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--jar', required=True, type=Path)
    args = parser.parse_args()
    jar = args.jar.resolve()
    if digest(jar.read_bytes()) != JAR_SHA256:
        raise SystemExit('Pinned TLA+ checksum mismatch')
    corpus_path = ROOT / 'research/evaluation/corpus.json'
    corpus = json.loads(corpus_path.read_text())
    source = (ROOT / corpus['source_path']).read_text()
    if digest(source.encode()) != corpus['baseline_source_sha256']:
        raise SystemExit('Frozen source changed; protocol amendment required')
    for path, expected in corpus['suite_files'].items():
        if digest((ROOT / path).read_bytes()) != expected:
            raise SystemExit(f'Frozen suite changed: {path}')
    upstream = subprocess.check_output(['git', 'show', corpus['upstream_commit']+':'+EXISTING[0]], cwd=ROOT)
    if digest(upstream) != corpus['suite_files'][EXISTING[0]]:
        raise SystemExit('Existing suite differs from upstream baseline')
    if RESULTS.exists():
        shutil.rmtree(RESULTS)  # Reproducible generated experiment output only.
    RESULTS.mkdir(parents=True)
    summary = {'schema': 1, 'execution_commit': subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
               'baseline_commit': corpus['baseline_commit'], 'corpus_sha256': digest(corpus_path.read_bytes()),
               'source_sha256': digest(source.encode()), 'suite_sha256': corpus['suite_files'],
               'model_sha256': {p.name:digest(p.read_bytes()) for p in (ROOT/'research/models').glob('*/*.tla')},
               'jar_sha256': JAR_SHA256, 'python': sys.version,
               'java': subprocess.run(['java','-version'],capture_output=True,text=True).stderr,
               'model_checking': 'Separate 13-configuration design experiment; unchanged model does not consume Python faults',
               'results': []}
    def record(row):
        summary['results'].append(row)
        (RESULTS/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
        print(json.dumps(row), flush=True)
    for name, code in [('baseline', source)] + [(f['id'], None) for f in corpus['faults']]:
        fault = next((f for f in corpus['faults'] if f['id'] == name), None)
        if fault:
            if source.count(fault['before']) != 1:
                raise SystemExit('Mutation anchor drift: '+name)
            code = source.replace(fault['before'], fault['after'])
        row = {'fault': name, 'implementation_sha256': digest(code.encode())}
        for arm, files in [('existing', EXISTING), ('expanded', EXPANDED)]:
            row[arm] = pytest_run(prepare(name,arm,code), files)
        if name == 'baseline' and any(row[a]['outcome'] != 'survived' for a in ('existing','expanded')):
            row['trace'] = {'outcome': 'inconclusive', 'reason': 'Baseline suites invalid; collection not attempted'}
            record(row)
            raise SystemExit('Invalid baseline; no fault may be scored')
        if fault:
            row['trace'] = trace_arm(code, fault, jar)
        else:
            groups = [trace_arm(code,dict(f,id='baseline-'+f['id']),jar)
                      for f in corpus['faults'] if f['trace_model']]
            row['trace'] = {'outcome': 'survived' if all(g['outcome']=='survived' for g in groups) else 'inconclusive', 'groups': groups}
        record(row)
        if name == 'baseline' and any(row[a]['outcome'] != 'survived' for a in ('existing','expanded','trace')):
            raise SystemExit('Invalid baseline; no fault may be scored')
    # Survivors and inconclusive mutants are research outcomes, not CI errors.
    # CI asserts execution integrity and the unchanged baseline only.


if __name__ == '__main__':
    main()
