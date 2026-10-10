"""Re-derive recovery outcomes from retained CI artifacts, without SDK execution."""
import base64
from collections import Counter
import hashlib
import io
import json
import os
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / 'research/discovery'
DIGESTS = {
    'temporal': '3639897379f0a03897d3f354f1d418fa5428707e2feb475c8421633c56eb1b39',
    'restate': 'eb4c2bc237801598e54224e726052c16d9985eeb1e535d6b788a6bfa13aa65d0',
}
ARMS = ('compatible_cancel', 'broken_cancel_restore', 'broken_force')


def check_engine(engine):
    raw = base64.b64decode((DIR / f'evidence-{engine}.zip.b64').read_bytes())
    assert hashlib.sha256(raw).hexdigest() == DIGESTS[engine], 'artifact digest'
    archive = zipfile.ZipFile(io.BytesIO(raw))
    def read(name):
        return archive.read(f'{engine}/{name}').decode()
    summary = json.loads(read('summary.json'))
    ledger = [json.loads(line) for line in read('ledger.jsonl').splitlines()]
    assert summary['run'] == '38059968219'
    assert len(summary['cases']) == 9
    assert {(r['repetition'], r['arm']) for r in summary['cases']} == {(i, a) for i in range(3) for a in ARMS}
    rows = []
    http = [json.loads(line) for line in read('http.jsonl').splitlines()] if engine == 'restate' else []
    for row in summary['cases']:
        assert row['error'] is None
        key, arm = row['key'], row['arm']
        effects = [e for e in ledger if e['key'] == key]
        counts = Counter(e['kind'] for e in effects)
        assert counts['effect'] == 1
        assert counts['cleanup'] == (0 if arm == 'broken_force' else 1)
        assert effects == row['ledger']
        assert counts['effect'] == row['effect_count'] and counts['cleanup'] == row['cleanup_count']
        mismatch = arm != 'compatible_cancel'
        if engine == 'temporal':
            events = json.loads(read(f'{key}-history.json'))['events']
            failures = [e for e in events if e.get('workflowTaskFailedEventAttributes', {}).get('cause')
                        == 'WORKFLOW_TASK_FAILED_CAUSE_NON_DETERMINISTIC_ERROR']
            assert bool(failures) == mismatch
            terminal = events[-1]['eventType']
            assert terminal == ('EVENT_TYPE_WORKFLOW_EXECUTION_TERMINATED' if arm == 'broken_force'
                                else 'EVENT_TYPE_WORKFLOW_EXECUTION_CANCELED')
            completed = []
            for e in events:
                attrs = e.get('activityTaskCompletedEventAttributes')
                if attrs:
                    completed.append(json.loads(base64.b64decode(attrs['result']['payloads'][0]['data'])))
            assert Counter(completed) == counts, 'history/ledger disagreement'
            controls = [e for e in events if e['eventType'] in (
                'EVENT_TYPE_WORKFLOW_EXECUTION_CANCEL_REQUESTED', 'EVENT_TYPE_WORKFLOW_EXECUTION_TERMINATED')]
            assert len(controls) == 1 and row['acknowledged'] is True
            if mismatch:
                assert int(failures[0]['eventId']) < int(controls[0]['eventId'])
            if arm == 'broken_cancel_restore':
                assert row['before_restore']['status'] == 'RUNNING'
                assert row['before_restore']['ledger'] == [{'key': key, 'kind': 'effect'}]
                assert any(int(e['eventId']) > int(controls[0]['eventId']) for e in failures), 'no post-cancel mismatch'
        else:
            invocation = row['invocation']
            operation = 'kill' if arm == 'broken_force' else 'cancel'
            controls = [r for r in http if r['method'] == 'PATCH' and r['url'].endswith(f'/{invocation}/{operation}')]
            assert len(controls) == 1 and controls[0]['status'] == 200
            snapshots = []
            for response in http:
                if response['url'].endswith('/query') and response['status'] == 200:
                    body = json.loads(response['body'])
                    for state in body['rows']:
                        if state.get('id') == invocation:
                            snapshots.append((response['time'], state))
            assert any(state.get('entry_type') == 'Command: GetPromise' for _, state in snapshots), 'wait barrier'
            failures = [(at, state) for at, state in snapshots if state.get('last_failure_error_code') == 'RT0016']
            assert bool(failures) == mismatch
            if mismatch:
                assert failures[0][0] < controls[0]['time']
            terminal_rows = [state for _, state in snapshots if state.get('status') == 'completed']
            assert terminal_rows and terminal_rows[-1] == row['terminal_state'][0]
            terminal = terminal_rows[-1]['completion_failure']
            assert terminal == ('[409] killed' if arm == 'broken_force' else '[409] cancelled')
            assert terminal_rows[-1]['completion_result'] == 'failure'
            if arm == 'broken_cancel_restore':
                before = row['before_restore']
                assert before['ledger'] == [{'key': key, 'kind': 'effect'}]
                assert before['state'][0]['status'] == 'backing-off'
                assert any(at - controls[0]['time'] >= 12 and state == before['state'][0] for at, state in snapshots)
        rows.append({'key': key, 'arm': arm, 'typed_mismatch_before_control': mismatch,
                     'terminal': terminal, 'effect_count': counts['effect'], 'cleanup_count': counts['cleanup']})
    return {'engine': engine, 'artifact_sha256': DIGESTS[engine], 'cases': rows}


def main():
    if os.environ.get('GITHUB_ACTIONS') != 'true':
        raise SystemExit('Run this audit in GitHub Actions')
    report = {'kind': 'retained_recovery_evidence_audit', 'source_run': '38059968219',
              'audit_run': os.environ['GITHUB_RUN_ID'], 'engines': [check_engine(e) for e in DIGESTS]}
    out = ROOT / 'research/results/discovery-audit'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print('DISCOVERY_AUDIT_JSON=' + json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
