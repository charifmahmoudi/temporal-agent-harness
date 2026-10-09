# Strengthening the model-to-code connection

[Walkthrough](../walkthrough.md) · [Correspondence](../correspondence.md) · [History model](../models/history/README.md)

This follow-up mechanically checks retained implementation observations and adds a
small durable-history model. It reuses frozen evidence; it is not a new independent
reproduction or a prospective prediction exercise.

| Check | Measured result | Supported conclusion |
| --- | --- | --- |
| Cleanup correspondence | Four retained caller-cancellation traces matched | Both child responses, under baseline and corrected code, admit executions of the corresponding Cleanup model |
| Model rejection controls | Eight rejected | Wrong cancellation semantics, invented approval, wrong input/order, and rewritten decision cannot explain the supplied observations |
| Projection validation | Three malformed records rejected | Missing child response, duplicate settlement, and premature tool-start evidence are not silently accepted |
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
