"""Retain/check the new TLC evidence separately from frozen experiment reports."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

from check_model import ROOT, JAR_SHA256
from check_cleanup_traces import module, require
from check_history_model import observations, evidence_module

EVAL = ROOT/'research/evaluation'
FILES = ['tests/cancellation/audit.py','research/scripts/check_cleanup_traces.py','research/scripts/check_history_model.py',
         'research/models/approval/Approval.tla','research/models/cancellation/Cleanup.tla',
         'research/models/history/History.tla']


def record():
    retained = {}
    for group in ('cleanup-conformance','history-model'):
        root = ROOT/'research/results'/group
        for path in sorted(root.rglob('*')):
            if not path.is_file() or any(p in {'tmp','states'} for p in path.relative_to(root).parts): continue
            if path.name in {'summary.json','observations.json','TLC.log'} or path.suffix == '.cfg' or path.name in {'CleanupTrace.tla','HistoryEvidence.tla'}:
                retained[group+'/'+path.relative_to(root).as_posix()] = path.read_text()
    bundle = {'schema':1,'method':'local retrospective TLC checks; original implementation runs unchanged',
              'hashes':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in FILES},'files':retained}
    (EVAL/'model-bridges.json.gz').write_bytes(gzip.compress(json.dumps(bundle,sort_keys=True).encode(),mtime=0))


def validate():
    bundle = json.loads(gzip.decompress((EVAL/'model-bridges.json.gz').read_bytes()))
    for path in FILES:
        require(bundle['hashes'][path] == hashlib.sha256((ROOT/path).read_bytes()).hexdigest(), 'bridge source drift: '+path)
    files = bundle['files']
    cleanup = json.loads(files['cleanup-conformance/summary.json'])
    history = json.loads(files['history-model/summary.json'])
    meta, rows = observations()
    require(json.loads(files['history-model/observations.json']) == rows, 'history observations drift')
    require(history['archive_sha256'] == meta['archive_sha256'], 'history archive mismatch')
    cm = json.loads((EVAL/'cancellation-results.json').read_text())
    require(cleanup['archive_sha256'] == cm['artifacts']['implementation']['sha256'], 'cleanup archive mismatch')
    require(len(cleanup['results']) == 12 and sum(r['matched'] for r in cleanup['results']) == 4, 'cleanup counts mismatch')
    require(len(cleanup['projection_rejections']) == 7 and len(history['results']) == 12 and history['cells'] == 36, 'bridge counts mismatch')
    for group,summary in [('cleanup-conformance',cleanup),('history-model',history)]:
        require(summary['jar_sha256'] == JAR_SHA256, 'jar mismatch')
        for result in summary['results']:
            prefix = group+'/'+result['case']+'/'
            log = files[prefix+'TLC.log']
            if group == 'cleanup-conformance':
                negative = result['expected_match']; invariant = 'TraceNotMatched'
                obs = json.loads(files[prefix+'observations.json'])
                require(files[prefix+'CleanupTrace.tla'] == module(obs), 'trace module drift')
            else:
                negative = result['expected_failure']; invariant = result['invariant']
            require(result['returncode'] == (12 if negative else 0), 'unexpected return code')
            message = f'Invariant {invariant} is violated' if negative else 'Model checking completed. No error has been found.'
            require(message in log, 'missing named TLC outcome')
    require(files['history-model/retained-evidence/HistoryEvidence.tla'] == evidence_module(rows), 'evidence module drift')
    return cleanup, history


def render():
    validate()
    return '''# Strengthening the model-to-code connection

[Walkthrough](../walkthrough.md) · [Correspondence](../correspondence.md) · [History model](../models/history/README.md)

This follow-up mechanically checks retained implementation observations and adds a
small durable-history model. It reuses frozen evidence; it is not a new independent
reproduction or a prospective prediction exercise.

| Check | Measured result | Supported conclusion |
| --- | --- | --- |
| Cleanup correspondence | Four retained caller-cancellation traces matched | Both child responses, under baseline and corrected code, admit executions of the corresponding Cleanup model |
| Model rejection controls | Eight rejected | Wrong cancellation semantics, invented approval, wrong input/order, and rewritten decision cannot explain the supplied observations |
| Projection validation | Seven invalid records rejected | Missing child response, duplicate settlement, premature dispatch, mismatched tool/evaluation identity, and duplicate ended/error terminals are rejected |
| History model | Twelve expected TLC results | Finite guarantees, expected counterexamples, a duplicate-effect fault, and evidence agreement behave as specified |
| Recorded replay comparison | All 36 cells agree | The model's command/marker rules explain the retained compatibility results within its restricted scope |

## What changed scientifically

Previously Cleanup had manual explanatory alignment only. The new checker lets TLC
search executable Cleanup transitions for a witness to each recorded input and
partial-state sequence. It binds the human decision and caller cancellation; only
ConsumeStep, FinishCleanup, and FinalizeStep may be hidden. The before snapshot
requires pending cleanup, and the after snapshot binds accepted status and outcome.
The two child responses remain one abstract action, with termination evidenced by
the probe's second-cancel and completed-caller observations.

The history model separates gate permission, activity-command recording, the single
ledger effect, and replay. It explains why C's fresh cancellation property and its
failure to preserve B's history can both hold. V preserves the modeled B histories
but fails the proposed universal C-to-V property. These are explicit finite checks,
not a general deployment theorem.

## Review follow-up: audit integrity (F05)

The projection now checks tool identity, matching evaluation start/terminal IDs,
and exactly one terminal across ended, superseded, and error events. These are
concrete preconditions for the single-call probe, not new Cleanup state variables
or a proof of general audit integrity. The projector is not a full event-schema
validator. Regression tests validate the added ended/error payloads against the
actual Pydantic classes, so those controls cannot be dismissed as invalid schemas.

The original [v1 snapshot](model-bridges-v1.json.gz) retains the pre-review checker
hash and its three projection controls. This refreshed snapshot adds four controls
and preserves the same four trace witnesses and eight model rejections. Original
implementation histories and scientific counterexamples are unchanged.

## Evidence and reproduction

Raw TLC logs, generated trace/evidence modules, configurations, observations,
source hashes, and summaries are retained in [model-bridges.json.gz](model-bridges.json.gz).
The original inputs remain in the [cancellation archive](cancellation-evidence/implementation.zip)
and [activity archive](activity-evidence.zip). The checks ran locally with Java 17
and the pinned TLA+ tools asset; CI repeats them in the model job.

```bash
python research/scripts/check_cleanup_traces.py --jar /path/to/tla2tools.jar
python research/scripts/check_history_model.py --jar /path/to/tla2tools.jar
python research/scripts/render_model_bridges.py --check
```

Fresh outputs go to `research/results/cleanup-conformance` and
`research/results/history-model`. `render_model_bridges.py --record` deliberately
replaces this retained snapshot after both complete runs; review changes before
committing. Normal documentation checks only validate the retained snapshot.

## Boundaries that remain

- The specification and projection rules are manual. This is not automatic code
  extraction, universal refinement, or proof of observer equivalence.
- Only the four completing caller-cancellation runs are checked against Cleanup.
  Closure, indefinitely blocked cleanup, and whole-workflow cancellation are not
  newly covered by this trace bridge. Earlier studies retain their separate evidence.
- History and Cleanup are separate abstractions; no formal composition theorem is
  claimed. History omits partial histories, worker routing, retries, crashes, and
  arbitrary external-effect semantics. Replay preserving effects is modeled as an
  assumption and challenged by a synthetic fault, not proved from SDK internals.
- The models were constructed with the measurements known. Agreement with those
  measurements strengthens internal consistency, not independent validation or
  scientific novelty. The frozen negative comparison remains unchanged.
'''


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--record',action='store_true'); parser.add_argument('--check',action='store_true')
    args = parser.parse_args()
    require(not (args.record and args.check), 'choose record or check')
    if args.record: record()
    text = render(); path = EVAL/'model-bridges.md'
    if args.check: require(path.read_text() == text, 'bridge report drift')
    else: path.write_text(text)
    print('Model bridges verified: 4 trace witnesses, 8 model rejections, 7 projection rejections, 12 history checks, 36 replay cells.')


if __name__ == '__main__': main()
