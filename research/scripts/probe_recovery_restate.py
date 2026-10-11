"""CI-only recovery probe using independently implemented Restate."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
import httpx

OUT = Path('research/results/discovery-recovery/restate').resolve()
HTTP = httpx.Client(timeout=10)
endpoint = None
log_file = None
sequence = 0


def request(method, url, **kwargs):
    response = HTTP.request(method, url, **kwargs)
    with (OUT / 'http.jsonl').open('a') as f:
        f.write(json.dumps({'time': time.time(), 'method': method, 'url': url,
                            'status': response.status_code, 'body': response.text}) + '\n')
    response.raise_for_status()
    return response


def query(table, key):
    data = request('POST', 'http://localhost:9070/query', json={'query': f"select * from {table} where id = '{key}'"},
                   headers={'accept': 'application/json'}).json()
    return data['rows'] if isinstance(data, dict) else data


def poll(fn, pred, seconds=60):
    deadline = time.monotonic() + seconds
    while True:
        value = fn()
        if pred(value):
            return value
        if time.monotonic() >= deadline:
            raise TimeoutError(repr(value))
        time.sleep(.25)


def stop():
    global endpoint, log_file
    if endpoint:
        endpoint.kill()
        endpoint.wait(timeout=10)
        endpoint = None
    if log_file:
        log_file.close()
        log_file = None


def start(broken=False):
    global endpoint, log_file, sequence
    stop()
    sequence += 1
    log_file = (OUT / f'endpoint-{sequence}-{broken}.log').open('w')
    endpoint = subprocess.Popen([sys.executable, 'research/scripts/discovery_restate_service.py'],
        env=dict(os.environ, DISCOVERY_OUTPUT=str(OUT), DISCOVERY_BROKEN='1' if broken else '0'),
        stdout=log_file, stderr=subprocess.STDOUT)
    def ready():
        if endpoint.poll() is not None:
            raise RuntimeError('Endpoint exited; inspect endpoint log')
        try:
            return HTTP.get('http://localhost:9080/discover', headers={'accept': 'application/vnd.restate.endpointmanifest.v3+json'}).status_code
        except httpx.ConnectError:
            return 0
    poll(ready, lambda x: x == 200)


def ledger(key):
    path = OUT / 'ledger.jsonl'
    return [json.loads(line) for line in path.read_text().splitlines()
            if json.loads(line)['key'] == key] if path.exists() else []


def action(key, operation):
    return request('PATCH', f'http://localhost:9070/invocations/{key}/{operation}').status_code


def trial(repetition, arm):
    key = f'discovery-{repetition}-{arm}'
    row = {'key': key, 'arm': arm, 'repetition': repetition, 'error': None}
    invocation = None
    try:
        start()
        result = request('POST', f'http://localhost:8080/DiscoveryRecovery/{key}/run/send', json=key).json()
        invocation = result['invocationId']
        row['invocation'] = invocation
        # The persisted GetPromise command follows the durably completed Run.
        row['barrier_journal'] = poll(lambda: query('sys_journal', invocation),
            lambda rows: any('GetPromise' in json.dumps(r) for r in rows))
        action(invocation, 'pause')
        poll(lambda: query('sys_invocation', invocation), lambda rows: rows and rows[0]['status'] == 'paused')
        start(arm != 'compatible_cancel')
        action(invocation, 'resume')
        if arm != 'compatible_cancel':
            row['mismatch_state'] = poll(lambda: query('sys_invocation', invocation),
                lambda rows: 'RT0016' in json.dumps(rows) or 'non-determinism' in json.dumps(rows).lower()
                or 'journal mismatch' in json.dumps(rows).lower())
        row['acknowledgement_status'] = action(invocation, 'kill' if arm == 'broken_force' else 'cancel')
        if arm == 'broken_cancel_restore':
            time.sleep(12)
            row['before_restore'] = {'state': query('sys_invocation', invocation), 'ledger': ledger(key)}
            start(False)
            action(invocation, 'resume')
        row['terminal_state'] = poll(lambda: query('sys_invocation', invocation),
                                    lambda rows: rows and rows[0]['status'] == 'completed')
        row['ledger'] = ledger(key)
        row['effect_count'] = sum(e['kind'] == 'effect' for e in row['ledger'])
        row['cleanup_count'] = sum(e['kind'] == 'cleanup' for e in row['ledger'])
        row['matches_prediction'] = row['effect_count'] == 1 and row['cleanup_count'] == (0 if arm == 'broken_force' else 1)
        if arm == 'broken_cancel_restore':
            row['matches_prediction'] &= bool(row['before_restore']['state']) and row['before_restore']['state'][0]['status'] != 'completed' and not any(e['kind'] == 'cleanup' for e in row['before_restore']['ledger'])
    except Exception as exc:
        row['error'] = {'type': type(exc).__name__, 'message': str(exc), 'traceback': traceback.format_exc()}
        if invocation:
            try:
                row['failure_state'] = query('sys_invocation', invocation)
                action(invocation, 'kill')
            except Exception:
                pass
    finally:
        stop()
    return row


def main():
    if os.environ.get('GITHUB_ACTIONS') != 'true':
        raise SystemExit('Run only in GitHub Actions')
    OUT.mkdir(parents=True, exist_ok=True)
    start()
    request('POST', 'http://localhost:9070/deployments', json={'uri': 'http://127.0.0.1:9080'})
    report = {'engine': 'restate', 'protocol': 1, 'commit': os.environ['GITHUB_SHA'],
              'run': os.environ['GITHUB_RUN_ID'], 'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'cases': []}
    try:
        for repetition in range(3):
            for arm in ('compatible_cancel', 'broken_cancel_restore', 'broken_force'):
                row = trial(repetition, arm)
                report['cases'].append(row)
                (OUT / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
                print('RECOVERY_CASE=' + json.dumps(row), flush=True)
    finally:
        stop()
    print('RECOVERY_PROBE_JSON=' + json.dumps(report), flush=True)
    if any(r['error'] or not r.get('matches_prediction') for r in report['cases']):
        raise SystemExit('Incomplete or prediction differs; inspect evidence')


if __name__ == '__main__':
    main()
