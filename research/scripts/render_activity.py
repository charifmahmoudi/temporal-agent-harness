"""Regenerate the v4 report only after checking its raw histories and effect ledger."""
import argparse
import base64
from collections import Counter
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import xml.etree.ElementTree as ET
import zipfile

from run_activity_study import history_projection, PATCH_ID, SCENARIOS

ROOT = Path(__file__).resolve().parents[2]
VARIANTS = ('baseline', 'corrected', 'versioned')


def read_history(archive, path):
    raw = archive.read(path).decode()
    return history_projection(SimpleNamespace(to_json=lambda: raw))


def validate():
    metadata = json.loads((ROOT / 'research/evaluation/activity-results.json').read_text())
    path = ROOT / 'research/evaluation' / metadata['archive']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == metadata['archive_sha256']
    with zipfile.ZipFile(path) as archive:
        summary = json.loads(archive.read('summary.json'))
        assert not summary['errors']
        assert summary['source_commit'] == metadata['checkout_sha']
        assert summary['runner_sha256'] == hashlib.sha256((ROOT / 'research/scripts/run_activity_study.py').read_bytes()).hexdigest()
        assert summary['process_sha256'] == hashlib.sha256((ROOT / 'research/scripts/activity_process.py').read_bytes()).hexdigest()
        assert summary['lock_sha256'] == hashlib.sha256((ROOT / 'uv.lock').read_bytes()).hexdigest()
        manifests = {v: json.loads(archive.read(v + '-manifest.json')) for v in VARIANTS}
        assert (ROOT / 'research/upstream/caller-cancellation-versioned.patch').read_bytes() == archive.read('versioned.patch')
        assert all(m['probe_sha256'] == hashlib.sha256((ROOT / 'tests/activity_upgrade/activity_probe.py').read_bytes()).hexdigest()
                   for m in manifests.values())
        fresh = summary['fresh']
        assert len(fresh) == 12
        assert {(r['variant'], r['scenario']) for r in fresh} == {(v, s) for v in VARIANTS for s in SCENARIOS}
        for row in fresh:
            case = row['case']
            assert row == json.loads(archive.read('cases/' + case + '/result.json'))
            assert row['history'] == read_history(archive, 'histories/' + case + '.history.json')
            ledger_path = 'cases/' + case + '/ledger.jsonl'
            actual = [json.loads(line) for line in archive.read(ledger_path).splitlines()] if ledger_path in archive.namelist() else []
            assert actual == row['ledger']
            assert all(e['source_sha256'] == manifests[row['variant']]['source_sha256'] and e['attempt'] == 1 for e in actual)
            expected = ('rejected' if row['scenario'] == 'deny' else 'cancelled'
                        if row['scenario'].startswith('second_') and row['variant'] != 'baseline' else 'dispatched')
            assert row['state']['outcome'] == expected
            assert row['state']['status'] == ('denied' if row['scenario'] == 'deny' else 'approved')
            assert len(actual) == len(row['history']['scheduled']) == len(row['history']['completed']) == int(expected == 'dispatched')
            assert len([e for e in row['state']['events'] if e['type'] == 'auto_approval_evaluation_superseded']) == 1
            if row['scenario'].startswith('second_'):
                assert row['state']['second_cancel'] and row['state']['caller_cancel_requested']
                assert len(row['history']['caller_signals']) == 1
                if actual:
                    assert row['history']['caller_signals'][0] < row['history']['scheduled'][0]
                if row['variant'] == 'versioned':
                    patches = [json.loads(base64.b64decode(m['details']['patch-data']['payloads'][0]['data']))
                               for m in row['history']['markers'] if m['markerName'] == 'core_patch']
                    assert patches == [{'id': PATCH_ID, 'deprecated': False}]
        replays = []
        for target in VARIANTS:
            result = json.loads(archive.read(target + '-replay.json'))
            assert result['manifest'] == manifests[target]
            assert len(result['rows']) == 12
            assert {r['history'] for r in result['rows']} == {r['case'] + '.history.json' for r in fresh}
            for row in result['rows']:
                assert row['target'] == target
                origin, scenario = row['history'].removesuffix('.history.json').split('--')
                measured_compatible = (scenario in {'approve', 'deny'} or origin == target
                                       or (origin == 'baseline' and target == 'versioned'))
                assert row['command'] == ('compatible' if measured_compatible else 'nondeterministic')
                assert row['history_sha256'] == hashlib.sha256(archive.read('histories/' + row['history'])).hexdigest()
                assert row['command'] in {'compatible', 'nondeterministic'}
                if row['command'] == 'nondeterministic':
                    assert 'NondeterminismError' in row['error']
                if row['history'].startswith(target + '--'):
                    assert row['command'] == 'compatible'
            replays.extend(result['rows'])
        assert Counter(r['command'] for r in replays) == {'compatible': 26, 'nondeterministic': 10}
        live = summary['live']
        assert len(live) == 8
        assert {(r['target'], r['mode'], r['cut']) for r in live} == {
            (v, s, c) for v in ('corrected', 'versioned') for s in ('second_raise', 'second_return')
            for c in ('before_cancel', 'after_activity')}
        for row in live:
            case = row['case']
            assert row == json.loads(archive.read('cases/' + case + '/result.json'))
            terminal = read_history(archive, 'cases/' + case + '/terminal.history.json')
            assert row['terminal_history'] == terminal
            ledger_path = 'cases/' + case + '/ledger.jsonl'
            actual = [json.loads(line) for line in archive.read(ledger_path).splitlines()] if ledger_path in archive.namelist() else []
            assert actual == row['ledger_after']
            assert all(e['source_sha256'] == manifests['baseline']['source_sha256'] and e['attempt'] == 1 for e in actual)
            expected_count = int(row['cut'] == 'after_activity')
            assert len(actual) == len(terminal['scheduled']) == len(terminal['completed']) == expected_count
            assert row['ledger_before'] == row['ledger_after']
            if row['target'] == 'corrected' and row['cut'] == 'after_activity':
                assert row['recovered']['recovery'] == 'nondeterministic'
                assert terminal['nondeterministic_tasks']
            else:
                assert row['recovered']['recovery'] == 'compatible'
                assert row['recovered']['state']['outcome'] == ('dispatched' if expected_count else 'cancelled')
                assert row['recovered']['state']['status'] == 'approved'
                if not expected_count:
                    assert row['recovered']['state']['caller_cancel_requested']
                    assert row['recovered']['state']['second_cancel']
        junit = ET.fromstring(archive.read('versioned-regressions.xml'))
        cases = list(junit.iter('testcase'))
        assert len(cases) == 375
        assert not any(c.find(tag) is not None for c in cases for tag in ('failure', 'error', 'skipped'))
        return metadata, summary, replays, len(cases)


def render():
    metadata, summary, replays, regressions = validate()
    matrix = []
    for origin in VARIANTS:
        cells = []
        for target in VARIANTS:
            group = [r for r in replays if r['target'] == target and r['history'].startswith(origin + '--')]
            cells.append(str(sum(r['command'] == 'compatible' for r in group)) + ' / 4')
        matrix.append('| ' + origin + ' | ' + ' | '.join(cells) + ' |')
    return r'''# Fixing cancellation without breaking durable history

[Case study](../../RESEARCH.md) · [Frozen protocol v4](activity-protocol.md) · [Properties](../properties.md)

## Finding

**The baseline can execute an activity after caller cancellation. A direct correction
prevents new execution but cannot replay the old activity-bearing history. A patch-
versioned correction preserves that history while enforcing cancellation on the new path.**

This is a concrete deployment constraint on the proposed fix. It is not a new Temporal
defect, a novel versioning technique, or evidence that a production deployment was affected.
The experiment uses a real harness activity tool and a test-only filesystem ledger.

Three implementation variants share the same workflow and stimuli:

| Variant | Behavior |
| --- | --- |
| B — baseline | Can consume the caller's cancellation during evaluator cleanup |
| C — direct correction | Propagates outstanding caller cancellation |
| V — versioned correction | Uses the existing SDK patch mechanism at the changed cancellation branch; preserves the old branch for unmarked baseline replay |

All corrections remain in isolated source copies. Production code on this branch
is unchanged by this experiment.

## Fresh execution: permission and cancellation are separate

| Scenario | B outcome; activity/ledger count | C outcome; activity/ledger count | V outcome; activity/ledger count |
| --- | --- | --- | --- |
| Ordinary approval | dispatched; 1 / 1 | dispatched; 1 / 1 | dispatched; 1 / 1 |
| Ordinary denial | rejected; 0 / 0 | rejected; 0 / 0 | rejected; 0 / 0 |
| Caller cancelled; child re-raises | dispatched; 1 / 1 | cancelled; 0 / 0 | cancelled; 0 / 0 |
| Caller cancelled; child returns | dispatched; 1 / 1 | cancelled; 0 / 0 | cancelled; 0 / 0 |

Both cancellation scenarios retain approved status and exactly one evaluation terminal
in every variant. The baseline cancellation signal is event 15, activity scheduling
is event 19, and completion is event 25. A recorded cleanup flag and second-cancellation
flag establish delivery, rather than treating a client request as sufficient evidence.
The activity writes and fsyncs one ledger record outside workflow memory. Server
history independently confirms scheduling and completion. V records patch identifier
`approval-caller-cancel-v1` on its new cancellation path.

## Replay: fresh-execution correctness is insufficient for an upgrade

Every one of the twelve fresh histories was replayed under every variant: **36 cells,
26 compatible and ten explicit nondeterminism results**. All twelve same-version
controls pass. The table shows compatible histories out of four per cell:

| History producer | Replay with B | Replay with C | Replay with V |
| --- | --- | --- | --- |
''' + '\n'.join(matrix) + r'''

Ordinary approval and denial are compatible in every direction. Incompatible cells
are the two caller-cancellation scenarios. For baseline history replayed under C,
the SDK explicitly reports **no command scheduled for event 19, ActivityTaskScheduled**.
The corrected code exits through cancellation and omits the command that the old
history requires. This is expected enforcement of Temporal's command contract.

V is compatible with all B histories and its own histories, but **not all histories
already produced by C**. C's unmarked cancellation history cannot be interpreted as
baseline dispatch history. Conversely, removing V's marker-aware code is not a
validated rollback path. The matrix therefore supports B → V for these cases, not
arbitrary migration among three versions.

## Live replacement: the durable boundary determines the outcome

The old worker is stopped gracefully; the new worker runs in a separate process
with verified source imports and workflow caching disabled. A checkpoint signal
forces reconstruction. Each row was exercised with both child cancellation responses.

| Baseline replacement point | New C worker | New V worker | Ledger after replacement |
| --- | --- | --- | --- |
| Cleanup entered; caller cancellation not yet delivered | New cancellation prevents scheduling | New cancellation prevents scheduling | 0 in all four cases |
| Activity completed; agent session still open | Workflow task fails with explicit nondeterminism | Old dispatch replays; session closes normally | Existing 1 retained; no second write in all four cases |

There are **eight live replacements**: six compatible recoveries and two explicit
nondeterministic workflow-task failures. Failed-task event 32 identifies the omitted
activity command. Those workflows are administratively terminated only after the
failure history is retained; termination is test cleanup, not a recovery outcome.
Final histories and final ledgers are checked after closing/termination, not only
at an early query. No additional activity schedule or ledger write was observed.

```mermaid
flowchart TD
    A["Approval accepted; evaluator cleanup"] --> K["Replacement before caller cancellation"]
    K --> N["C or V: newly delivered cancellation; no activity"]
    A --> B["Baseline consumes cancellation"]
    B --> E["Activity scheduled and ledger written"]
    E --> C["Replace with C: command missing; task fails"]
    E --> V["Replace with V: old command matches; no new write"]
```

**Figure.** The accepted approval is unchanged along both branches. The relevant
upgrade boundary is whether the cancellation-sensitive activity command is already
part of history. Only the two stated replacement points were tested.

## Obligations and their limits

For invocation i, D(i) means caller cancellation delivered during cleanup, S(i)
means a scheduled activity command, and E(i) means the recorded ledger effect.
For a newly executing corrected branch, the required safety obligation is

$$D(i)\Rightarrow\neg S(i).$$

The baseline supplies two counterexamples with D(i), S(i), and E(i). C and V satisfy
the obligation for the tested fresh and pre-cancellation replacement executions.
These are implementation experiments, not a proof over all schedules.

Let R(h,v) mean command-compatible replay of history h under version v. The
baseline caller histories provide witnesses to

$$R(h,B)\land\neg R(h,C)\land R(h,V).$$

Versioning preserves historical commands; it does not retroactively make those
commands satisfy the new cancellation contract. V intentionally reproduces the old
dispatch during baseline replay without executing the completed activity again.
Preserving old history and preventing future dispatch are distinct obligations.
The earlier Cleanup TLA+ model checks invocation cancellation; it does not model
history matching, activity retries, or patch-marker semantics. No new refinement
proof or model-led discovery is claimed.

## Evidence, validation, and reproduction

''' + f"The final measured [CI run {metadata['run_id']}]({metadata['run_url']}) used\n" + f"PR head `{metadata['head_sha']}` and checkout\n`{metadata['checkout_sha']}` (the PR merge revision).\n" + f"All {regressions} existing harness regressions passed against isolated V source;\n" + r'''three experiment-scoring controls also pass. The frozen lockfile specifies Temporal
SDK 1.32.0. The time-skipping server's simulated timestamps are not wall-clock
measurements; causal claims use delivered-input state and event IDs.

The [retained archive](activity-evidence.zip) contains all histories, live prefixes,
worker logs, ledger writes, replay diagnostics, source manifests, proposed diffs,
and regression JUnit results. The [provenance record](activity-results.json) identifies
the protocol commit, exact artifact digest, and measured revision. Documentation CI
recomputes counts and outcome tables from the raw records and verifies source hashes.

```bash
uv sync --frozen
uv run --frozen pytest tests/activity_upgrade/test_scoring.py -q
uv run --frozen python research/scripts/run_activity_study.py
cd research/results/activity-upgrade/variants/versioned
PYTHONPATH="$PWD" ../../../../../.venv/bin/python run_regressions.py \
  ../../versioned-manifest.json ../../versioned-regressions.xml
```

Use a clean checkout/output directory: the runner refuses to reuse old results.
The [CI workflow](../../.github/workflows/activity-upgrade.yml) is the authoritative
execution recipe. From the root, `python research/scripts/render_activity.py --check`
verifies this report against retained evidence without starting Temporal.

## Scientific and maintainer assessment

**For maintainers:** the direct cancellation fix is not, by itself, a validated
upgrade for these old histories. The V experiment demonstrates one bounded remedy
and exposes a migration constraint if C has already run. Review the intended caller
contract, patch placement, worker routing, and supported history cohorts before any
deployment. The original minimal patch remains useful but carries this rollout caveat.

**For scientific review:** the result connects a real cancellation defect, a durable
command mismatch, and a tested compatibility remedy. This is stronger practical
evidence than workflow-local outcome drift. It does not demonstrate novel patching,
superior formal-method fault detection, or cross-framework generality. The discrepancy
was investigated through a declared experiment following the earlier inspection-led
finding. The frozen comparison's negative result remains unchanged.

The study covers one activity, one invocation, no retries, two controlled child
responses, and graceful nonsticky replacement. It does not establish crash recovery,
exactly-once external effects, rollback, production sticky routing, concurrent mixed
workers, or arbitrary historical cohorts. Independent contract review, external
reproduction, and upstream feedback remain the next gates.
'''


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    text = render()
    output = ROOT / 'research/evaluation/activity-results.md'
    if args.check:
        assert output.read_text() == text, 'Activity report drifted from raw evidence'
        print('Activity evidence verified: 12 fresh, 36 replay, 8 live, 375 harness regressions.')
    else:
        output.write_text(text)
