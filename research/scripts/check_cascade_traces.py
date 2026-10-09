"""Match coupled-gate observations against Cascade, including policy and event order.

Hidden model steps are permitted. A witness establishes existential consistency of
partial observations; it is not a claim that the recorded action sequence is complete.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from check_model import ROOT, JAR_SHA256

SCENARIOS = {'remember_first', 'evaluator_deny_first', 'human_deny_first', 'denied_remember',
             'policy_relax', 'tighten_after_release', 'different_tool', 'close_first', 'remember_then_close'}


def predicate(observation):
    state = observation['state']
    if set(state) != {'status', 'closed', 'allowed', 'history', 'phase'}:
        raise ValueError('Unexpected projection fields')
    if set(state['status']) != {'a', 'b'} or type(state['closed']) is not bool:
        raise ValueError('Malformed call/closure projection')
    terms = []
    for call, status in state['status'].items():
        if status not in {'pending', 'approved', 'denied'}:
            raise ValueError('Unknown status')
        terms.append(f'status[{call}] = {json.dumps(status)}')
    for call, phase in state['phase'].items():
        if call not in {'a', 'b'} or phase not in {'dispatched', 'rejected'}:
            raise ValueError('Unknown caller outcome')
        terms.append(f'phase[{call}] = {json.dumps(phase)}')
    if len(state['allowed']) != len(set(state['allowed'])) or not set(state['allowed']) <= {'shared', 'other'}:
        raise ValueError('Unknown or duplicate allowed tool')
    if any(call not in {'a', 'b'} for call in state['history']):
        raise ValueError('Unknown call in history')
    terms.extend([
        'closed = ' + ('TRUE' if state['closed'] else 'FALSE'),
        'allowed = {' + ', '.join(json.dumps(t) for t in sorted(state['allowed'])) + '}',
        'history = <<' + ', '.join(state['history']) + '>>',
    ])
    return ' /\\ '.join(terms)


def check(jar, observations, name, different, expected):
    out = ROOT / 'research/results/cascade-conformance' / name
    out.mkdir(parents=True, exist_ok=True)
    tmp = out / 'tmp'
    tmp.mkdir(exist_ok=True)
    shutil.copy(ROOT / 'research/models/approval/Approval.tla', out / 'Approval.tla')
    shutil.copy(ROOT / 'research/models/cascade/Cascade.tla', out / 'Cascade.tla')
    cases = '\n'.join(f' [] cursor = {i} -> ({predicate(o)})' for i, o in enumerate(observations))
    (out / 'CascadeTrace.tla').write_text(f'''---------------- MODULE CascadeTrace ----------------
EXTENDS Cascade
VARIABLE cursor
traceVars == <<cascadeVars, cursor>>
Match == CASE FALSE -> FALSE
{cases}
 [] OTHER -> FALSE
Advance == /\\ cursor < {len(observations)} /\\ Match
           /\\ cursor' = cursor + 1 /\\ UNCHANGED cascadeVars
Hidden == /\\ CascadeNext /\\ UNCHANGED cursor
TraceSpec == CascadeInit /\\ cursor = 0 /\\ [][Hidden \\/ Advance]_traceVars
TraceNotMatched == cursor < {len(observations)}
=====================================================
''')
    config = (ROOT / 'research/models/cascade' / ('DifferentTools.cfg' if different else 'SameTool.cfg')).read_text()
    config = config.replace('SPECIFICATION CascadeSpec', 'SPECIFICATION TraceSpec')
    config = config.replace('INVARIANTS CascadeTypeOK DecisionStable SingleResolution AuthorizedDispatch DeniedNeverDispatches ScopePreserved CauseBeforeCascade', 'INVARIANT TraceNotMatched')
    (out / 'CascadeTrace.cfg').write_text(config)
    run = subprocess.run(['java', f'-Djava.io.tmpdir={tmp}', '-XX:+UseParallelGC', '-cp', str(jar),
                          'tlc2.TLC', '-workers', '1', '-seed', '1', '-config', 'CascadeTrace.cfg', 'CascadeTrace.tla'],
                         cwd=out, capture_output=True, text=True, timeout=120)
    log = run.stdout + run.stderr
    (out / 'TLC.log').write_text(log)
    matched = run.returncode == 12 and 'Invariant TraceNotMatched is violated' in log
    exhausted = run.returncode == 0 and 'Model checking completed. No error has been found.' in log
    if not (matched if expected else exhausted):
        raise RuntimeError(f'{name}: unexpected TLC result {run.returncode}; see {out}')
    return dict(case=name, expected_match=expected, matched=matched, returncode=run.returncode)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--jar', required=True, type=Path)
    args = p.parse_args()
    jar = args.jar.resolve()
    if hashlib.sha256(jar.read_bytes()).hexdigest() != JAR_SHA256:
        raise SystemExit('Unexpected TLA+ tools checksum')
    traces = [json.loads(p.read_text()) for p in sorted((ROOT / 'research/results/cascade-traces').glob('*.json'))]
    if len(traces) != len(SCENARIOS) or {t.get('scenario') for t in traces} != SCENARIOS:
        raise SystemExit('Missing/duplicate/unexpected traces')
    source_hash = hashlib.sha256((ROOT / 'temporal_agent_harness/harness/agent_workflow.py').read_bytes()).hexdigest()
    results = []
    for trace in traces:
        if trace.get('schema') != 1 or trace.get('implementation_sha256') != source_hash or len(trace.get('outcomes', {})) != 2:
            raise SystemExit('Incomplete/stale/unsupported trace')
        if not trace['observations'] or set(trace['observations'][-1]['state']['phase']) != {'a', 'b'}:
            raise SystemExit('Missing terminal projection')
        results.append(check(jar, trace['observations'], trace['scenario'], trace['different_tools'], True))
    def observation(a, b, phase=None):
        return {'state': {'status': {'a': a, 'b': b}, 'closed': False, 'allowed': [],
                          'history': ['a'], 'phase': phase or {}}}
    results.append(check(jar, [observation('denied', 'pending', {'a': 'dispatched'})], 'negative_denied_dispatch', False, False))
    results.append(check(jar, [observation('denied', 'pending'), observation('approved', 'pending')],
                         'negative_denial_overwritten', False, False))
    out = ROOT / 'research/results/cascade-conformance/summary.json'
    out.write_text(json.dumps({'module_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in [ROOT / 'research/models/approval/Approval.tla', ROOT / 'research/models/cascade/Cascade.tla']},
                         'results': results}, indent=2) + '\n')
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
