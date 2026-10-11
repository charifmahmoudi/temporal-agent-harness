"""Retrospective one-decision feasibility pilot, not a Temporal patch synthesizer.

For a declared observable vocabulary, find a Boolean command decision consistent
with every supplied row or return a conflicting pair. This is a standard finite
function-consistency check, not a claimed new synthesis algorithm.
"""
import argparse
from copy import deepcopy
import hashlib
from itertools import combinations, product
import json
from pathlib import Path

from check_history_model import observations

ROOT = Path(__file__).resolve().parents[2]
FEATURES = ('approved', 'cancelled', 'patch_branch')
RESULT = ROOT / 'research/evaluation/repair-observability.json'


def solve(rows, features):
    """Exact only for a single total Boolean decision on the supplied finite rows."""
    groups = {}
    for row in sorted(rows, key=lambda r: r['id']):
        key = tuple(row['observed'][f] for f in features)
        required = row['required_command']
        if key in groups and groups[key]['required_command'] != required:
            return {'feasible': False, 'conflict': [groups[key]['id'], row['id']],
                    'observation': list(key)}
        groups.setdefault(key, row)
    return {'feasible': True, 'table': [
        {'observation': list(key), 'command': row['required_command']}
        for key, row in sorted(groups.items())]}


def brute_force(rows, features):
    """Independent oracle: enumerate total truth tables, not collision groups."""
    domain = list(product((False, True), repeat=len(features)))
    for outputs in product((False, True), repeat=len(domain)):
        if all(outputs[domain.index(tuple(r['observed'][f] for f in features))]
               == r['required_command'] for r in rows):
            return True
    return False


def retained_rows():
    meta, cells = observations()
    unique = {}
    for cell in cells:
        name = cell['id'].rsplit('--', 1)[0]
        row = {'id': name, 'producer': cell['producer'], 'kind': 'retained-replay',
               'observed': {'approved': cell['approved'], 'cancelled': cell['cancelled'],
                            'patch_branch': cell['marker']},
               'required_command': cell['command'], 'history_sha256': cell['history_sha256']}
        if name in unique and unique[name] != row:
            raise ValueError('target-dependent input projection')
        unique[name] = row
    if len(unique) != 12:
        raise ValueError('expected twelve distinct retained histories')
    return meta, list(unique.values())


def fresh_rows():
    # Policy constraints, NOT newly executed observations. At the candidate
    # cancellation branch a newly introduced patch would select its new path.
    return [{'id': 'fresh-' + name, 'producer': 'fresh', 'kind': 'synthetic-policy',
             'observed': {'approved': a, 'cancelled': c, 'patch_branch': c},
             'required_command': a and not c}
            for name, a, c in [('approve', True, False), ('deny', False, False),
                              ('cancel', True, True)]]


def analyze(rows):
    results = []
    for size in range(len(FEATURES) + 1):
        for features in combinations(FEATURES, size):
            answer = solve(rows, features)
            if answer['feasible'] != brute_force(rows, features):
                raise ValueError('solver/oracle disagreement')
            results.append({'features': list(features), **answer})
    feasible = [r for r in results if r['feasible']]
    minimum = min((len(r['features']) for r in feasible), default=None)
    return {'rows': [r['id'] for r in rows], 'feature_subsets': results,
            'minimum_feature_sets': [r['features'] for r in feasible
                                     if len(r['features']) == minimum]}


def evidence():
    meta, retained = retained_rows()
    scenarios = {}
    for name, producers in [('B', {'baseline'}), ('C', {'corrected'}),
                            ('B_V', {'baseline', 'versioned'}),
                            ('C_V', {'corrected', 'versioned'}),
                            ('B_C_V', {'baseline', 'corrected', 'versioned'})]:
        scenarios[name] = analyze([r for r in retained if r['producer'] in producers] + fresh_rows())
    full = solve(retained + fresh_rows(), FEATURES)
    if full['feasible']:
        raise ValueError('mixed-cohort negative control unexpectedly feasible')
    # Deliberately leaking the answer removes conflicts; never use this as a
    # realizable input to a workflow guard or count it as a proposed remedy.
    leaked = deepcopy(retained + fresh_rows())
    for row in leaked:
        row['observed']['oracle_command'] = row['required_command']
    if not solve(leaked, ('oracle_command',))['feasible']:
        raise ValueError('oracle leakage control failed')
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in [Path(__file__), ROOT/'research/scripts/check_history_model.py']}
    return {'schema': 1, 'status': 'retrospective restricted-grammar diagnostic; novelty not established',
            'archive_sha256': meta['archive_sha256'], 'source_sha256': hashes,
            'features': list(FEATURES), 'retained': retained, 'fresh_policy': fresh_rows(),
            'scenarios': scenarios, 'oracle_leakage_control': 'feasible but inadmissible',
            'oracle_comparisons': sum(len(s['feature_subsets']) for s in scenarios.values())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = evidence()
    if args.check:
        if json.loads(RESULT.read_text()) != result:
            raise SystemExit('repair-observability evidence drift')
    else:
        RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    for name, row in result['scenarios'].items():
        print(name + ': minimum feature sets ' + str(row['minimum_feature_sets']))
    print('40 feature-subset verdicts agree with exhaustive truth-table enumeration.')


if __name__ == '__main__':
    main()
