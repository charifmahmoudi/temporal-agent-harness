"""Validate retained histories and derive the frozen pilot's descriptive metrics."""
import argparse
import base64
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def summarize(bundle):
    result = {'run_url': bundle['run_url'], 'protocol_commit': bundle['protocol_commit'], 'arms': []}
    server_hashes = set()
    runner_hashes = set()
    for report in bundle['reports']:
        assert report['infrastructure_error'] is None
        assert len(report['rows']) == 36
        server_hashes.add(report['server_sha256'])
        runner_hashes.add(report['runner_sha256'])
        keys = set()
        for row in report['rows']:
            key = (row['seed'], row['method'], row['index'])
            assert key not in keys
            keys.add(key)
            expected = report['plan'][str(row['seed'])][row['method']][row['index']-1]
            assert [row['latency'], row['update_delay']] == expected
            if 'history_gzip_base64' not in row:
                assert row['verdict'] == 'inconclusive_collection'
                continue
            raw = gzip.decompress(base64.b64decode(row['history_gzip_base64']))
            assert hashlib.sha256(raw).hexdigest() == row['history_sha256']
            events = json.loads(raw)['events']
            scheduled = [int(e['eventId']) for e in events if 'activityTaskScheduledEventAttributes' in e]
            completed = [int(e['eventId']) for e in events if 'activityTaskCompletedEventAttributes' in e]
            accepted = [e['workflowExecutionUpdateAcceptedEventAttributes'] for e in events
                        if 'workflowExecutionUpdateAcceptedEventAttributes' in e]
            sequencing = int(accepted[0]['acceptedRequestSequencingEventId']) if len(accepted) == 1 else None
            assert scheduled == row['scheduled_ids'] and completed == row['completed_ids']
            assert sequencing == row['update_sequencing_id']
            assert row['coverage'] == [row['resumed'], bool(completed and sequencing and completed[0] < sequencing)]
            live_ok = isinstance(row['resumed'], bool) and row['finished'] == (2 if row['resumed'] else 1) and len(scheduled) == len(completed) == row['finished']
            if not live_ok:
                assert row['verdict'] == 'inconclusive_live_precondition'
            elif row['verdict'] == 'nondeterministic':
                assert row['exception_type'] == 'NondeterminismError'
            elif row['verdict'] == 'compatible':
                assert row['exception_type'] is None
            else:
                assert row['verdict'] == 'inconclusive_replay_error'
        methods = []
        for method in ('systematic', 'random', 'regression'):
            rows = [r for r in report['rows'] if r['method'] == method]
            first, first_seconds, coverage, prefix = [], [], [], [0]*4
            for seed in range(3):
                group = sorted([r for r in rows if r['seed'] == seed], key=lambda r:r['index'])
                assert [r['index'] for r in group] == [1,2,3,4]
                detections = [r['index'] for r in group if r['verdict'] == 'nondeterministic']
                first.append(min(detections) if detections else None)
                first_seconds.append(round(sum(r.get('total_seconds', 0) for r in group if r['index'] <= min(detections)), 3) if detections else None)
                coverage.append(len({tuple(r['coverage']) for r in group if 'coverage' in r and not r['verdict'].startswith('inconclusive')}))
                for i in range(4):
                    prefix[i] += bool(detections and min(detections) <= i+1)
            methods.append({'method': method, 'verdicts': dict(Counter(r['verdict'] for r in rows)),
                'first_detection_by_seed': first, 'first_detection_trial_seconds': first_seconds,
                'repetitions_detecting_by_budget': prefix,
                'coverage_by_seed': coverage,
                'trial_seconds': round(sum(r.get('total_seconds',0) for r in rows),3),
                'replay_seconds': round(sum(r.get('replay_seconds',0) for r in rows),3),
                'missing_trial_times': sum('total_seconds' not in r for r in rows)})
        result['arms'].append({'sdk': report['sdk'], 'setup_seconds': report['setup_seconds'],
            'total_seconds': report['total_seconds'], 'methods': methods})
    assert len(server_hashes) == len(runner_hashes) == 1
    result['server_sha256'] = next(iter(server_hashes))
    result['runner_sha256'] = next(iter(runner_hashes))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    bundle = json.loads((ROOT/'evaluation/recovery-comparison-evidence.json').read_text())
    result = summarize(bundle)
    target = ROOT/'evaluation/recovery-comparison-summary.json'
    expected = json.dumps(result,indent=2)+'\n'
    if args.check:
        assert target.read_text() == expected, 'Summary differs from retained evidence'
        print('Recovery comparison: 72 histories verified; summary matches evidence.')
    else:
        target.write_text(expected)
        print(json.dumps(result, indent=2))
