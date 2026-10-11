"""Validate recorded inputs and partial states against the actual Cascade actions.

Only Consume, Cancelled, and Finalize may occur without an observation. Human,
remember, policy, closure, and evaluator-completion actions must come from recorded
inputs. This remains bounded trace conformance, not a Python refinement proof.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from check_model import ROOT, JAR_SHA256

SCENARIOS = {'remember_first', 'evaluator_deny_first', 'human_deny_first', 'denied_remember',
             'policy_relax', 'tighten_after_release', 'different_tool', 'close_first', 'remember_then_close',
             'evaluator_approve_first', 'evaluator_escalate_first', 'evaluator_error_first'}
ORDERS = {('a', 'b'), ('b', 'a')}


def predicate(observation):
    """Read a projection literally; never infer unobserved evaluator/gate state."""
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


def recorded_action(observation):
    """Bind model actions to actual handler inputs, rejecting unsupported metadata."""
    action = observation['action']
    if action is None:
        return 'UNCHANGED cascadeVars'
    kind = action.get('kind')
    if kind == 'close' and set(action) == {'kind'}:
        return 'BaseStep /\\ Close'
    if kind == 'policy' and set(action) == {'kind', 'allowed'}:
        if not set(action['allowed']) <= {'shared', 'other'}:
            raise ValueError('Unknown tool in policy input')
        return 'Update({' + ', '.join(json.dumps(t) for t in sorted(action['allowed'])) + '})'
    call = action.get('call')
    if call not in {'a', 'b'}:
        raise ValueError('Unknown action call')
    if kind in {'human', 'remember'} and set(action) == {'kind', 'call', 'approved'}:
        if type(action['approved']) is not bool or (kind == 'remember' and not action['approved']):
            raise ValueError('Malformed decision input')
        if kind == 'remember':
            return f'Remember({call})'
        decision = 'approved' if action['approved'] else 'denied'
        return f'BaseStep /\\ Human({call}, "{decision}")'
    if kind == 'complete' and set(action) == {'kind', 'call', 'verdict'}:
        if action['verdict'] not in {'approve', 'deny', 'escalate', 'error'}:
            raise ValueError('Unknown evaluator result')
        return f'BaseStep /\\ Complete({call}, {json.dumps(action["verdict"])})'
    raise ValueError('Unsupported recorded action')


def check(jar, observations, name, different, expected, order=('a', 'b')):
    """A named TLC invariant violation witnesses cursor completion; exhaustion rejects."""
    out = ROOT / 'research/results/cascade-conformance' / name
    out.mkdir(parents=True, exist_ok=True)
    tmp = out / 'tmp'
    tmp.mkdir(exist_ok=True)
    shutil.copy(ROOT / 'research/models/approval/Approval.tla', out / 'Approval.tla')
    shutil.copy(ROOT / 'research/models/cascade/Cascade.tla', out / 'Cascade.tla')
    # Action and successor projection must match at the same cursor step. Hidden
    # steps cannot invent new inputs or evaluator results to repair a bad trace.
    definitions = '\n'.join(f'Observed{i} == {predicate(o)}' for i, o in enumerate(observations))
    steps = '\n \\/ '.join(f'(cursor = {i} /\\ ({recorded_action(o)}) /\\ Observed{i}\' /\\ cursor\' = {i + 1})'
                            for i, o in enumerate(observations))
    (out / 'CascadeTrace.tla').write_text(f'''---------------- MODULE CascadeTrace ----------------
EXTENDS Cascade
VARIABLE cursor
traceVars == <<cascadeVars, cursor>>
{definitions}
Advance == {steps}
Hidden == /\\ BaseStep /\\ (\\E c \\in Calls : Consume(c) \\/ Cancelled(c) \\/ Finalize(c))
          /\\ UNCHANGED cursor
TraceSpec == CascadeInit /\\ cursor = 0 /\\ [][Hidden \\/ Advance]_traceVars
TraceNotMatched == cursor < {len(observations)}
=====================================================
''')
    config = (ROOT / 'research/models/cascade' / ('DifferentTools.cfg' if different else 'SameTool.cfg')).read_text()
    config = config.replace('SPECIFICATION CascadeSpec', 'SPECIFICATION TraceSpec')
    if tuple(order) == ('b', 'a'):
        config = config.replace('CallOrder <- OrderedCalls', 'CallOrder <- ReversedCalls')
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
        print(log[-6000:])  # Keep CI diagnosis useful without flooding successful runs.
        raise RuntimeError(f'{name}: unexpected TLC result {run.returncode}; see {out}')
    return dict(case=name, expected_match=expected, matched=matched, returncode=run.returncode)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--jar', required=True, type=Path)
    jar = p.parse_args().jar.resolve()
    if hashlib.sha256(jar.read_bytes()).hexdigest() != JAR_SHA256:
        raise SystemExit('Unexpected TLA+ tools checksum')
    traces = [json.loads(p.read_text()) for p in sorted((ROOT / 'research/results/cascade-traces').glob('*.json'))]
    expected_cases = {(s, o) for s in SCENARIOS for o in ORDERS}
    cases = {(t.get('scenario'), tuple(t.get('registration_order', []))) for t in traces}
    if len(traces) != len(expected_cases) or cases != expected_cases:
        raise SystemExit('Missing/duplicate/unexpected traces (clean stale output before regeneration)')
    source_hash = hashlib.sha256((ROOT / 'temporal_agent_harness/harness/agent_workflow.py').read_bytes()).hexdigest()
    results = []
    for trace in traces:
        if trace.get('schema') != 2 or trace.get('implementation_sha256') != source_hash or set(trace.get('outcomes', {})) != {'a', 'b'}:
            raise SystemExit('Incomplete/stale/unsupported trace')
        if not trace['observations'] or trace['observations'][-1]['state']['phase'] != trace['outcomes']:
            raise SystemExit('Missing/inconsistent terminal projection')
        order = trace['registration_order']
        results.append(check(jar, trace['observations'], trace['scenario'] + '_' + ''.join(order),
                             trace['different_tools'], True, order))

    def observation(a, b, phase=None, action=None, history=('a',), allowed=()):
        return {'action': action, 'state': {'status': {'a': a, 'b': b}, 'closed': False,
                'allowed': list(allowed), 'history': list(history), 'phase': phase or {}}}

    denial = {'kind': 'human', 'call': 'a', 'approved': False}
    results.append(check(jar, [observation('denied', 'pending', {'a': 'dispatched'}, denial)],
                         'negative_denied_dispatch', False, False))
    results.append(check(jar, [observation('denied', 'pending', action=denial), observation('approved', 'pending')],
                         'negative_denial_overwritten', False, False))
    results.append(check(jar, [observation('approved', 'approved', history=('a', 'b'), allowed=('shared',))],
                         'negative_unrecorded_policy', False, False))
    results.append(check(jar, [observation('approved', 'approved', action={'kind': 'remember', 'call': 'a', 'approved': True},
                                         history=('b', 'a'), allowed=('shared',))],
                         'negative_wrong_cause', False, False))
    results.append(check(jar, [observation('approved', 'pending', action=denial)],
                         'negative_wrong_input', False, False))
    out = ROOT / 'research/results/cascade-conformance/summary.json'
    out.write_text(json.dumps({'schema': 2, 'hidden_actions': ['Consume', 'Cancelled', 'Finalize'],
                             'module_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                             for p in [ROOT / 'research/models/approval/Approval.tla', ROOT / 'research/models/cascade/Cascade.tla']},
                             'results': results}, indent=2) + '\n')
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
