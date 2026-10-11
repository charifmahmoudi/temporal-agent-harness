# Comparative findings and publication decision

[Measured results](results-v1.md) · [Frozen protocol](protocol.md) · [Review packet](review-packet.md)

## Finding

The first comparison **does not demonstrate additional fault detection beyond
expanded tests**. It demonstrates that three Python faults produce model-incompatible
traces, while exposing limitations in the collection and scoring procedures. This is
an exploratory six-fault case study, not a representative benchmark.

The unchanged implementation passed 23 existing tests, 82 expanded tests, and eight
selected trace checks across five scenario groups. The measured matrix reports two
existing-test detections, five expanded-test detections, three trace detections, two
trace inconclusive cases, and one trace exclusion. Trace-only detections are zero.
The report and JSON retain the exact execution revision and CI evidence.

## Explain the inconclusive cases

| Case | Observed failure | Scientific interpretation |
| --- | --- | --- |
| denial_remember trace | Collector's later decision update fails after unintended sibling settlement. | Fixed stimuli assume a still-pending call. The collector aborts before writing the trace; this is not TLC detection. |
| scope_leak trace | Collector's later denial update fails after unintended cross-tool approval. | Same observation-loss problem. The fault is behaviorally visible but the trace arm cannot score it. |
| unvalidated_superseded expanded tests | First superseded-result regression raises `AttributeError` in the mutated production method. | The suite flags the actual defect, but v1 only credits assertion failures and stops at the first failure. Its score is inconclusive, not a claim that tests are blind to the defect. |

The malformed fault's trace arm is explicitly out of scope because the models assume
valid evaluator inputs. It is not a trace-checking survivor. The prior targeted
mutation experiment still separately demonstrates detection using a Temporal
assertion-based reproducer; these experiments use different scoring and execution
orders and must not be conflated.

## What the comparison supports

Expanded scenarios add three scored detections beyond the existing suite: denial
remembering, scope leakage, and publication reversal. The model layer independently
rejects publication reversal, closure approval, and denial-as-approval observations
against the stated contract. These results establish selected regression sensitivity
and contract checking; they do not establish superiority, diagnostic advantage,
schedule completeness, or predictive defect-detection rates.

The two newly selected boundary faults are already detected by the existing tests.
This weakens any argument that adding formalism was necessary to expose those faults.
The first four cases were known pilot cases; the corpus has strong selection bias.
No false-positive rate is estimated from one fixed baseline.

## Next experiment, with a new protocol

The subsequent [cancellation investigation](cancellation-results.md) is complete as a
separate lifecycle study. It reproduces caller cancellation being swallowed during
cleanup and validates an isolated correction. Its protocol, model, and results do not
amend v1's fault corpus or scores. The collector and scoring improvements below remain
future work for a second **comparative** experiment.

Preserve v1. A v2 protocol should capture partial observations before a later stimulus
can fail, record update failure as an explicit observed outcome, and test both
registration orders even if the first aborts. Before scoring faults, prove with
controls that recording itself does not invent an input or change scheduling.
Do not adapt the valid-input model to accept the malformed-result case silently.

Scoring also needs a predeclared distinction between a defect-triggered exception in
the subject and an exception in fixture/collector infrastructure. A new result must
retain v1's conservative score and document the additional evidence, rather than
retroactively changing it. Add an independently designed corpus or use hidden fault
selection to reduce author bias. Measure diagnostic usefulness and effort separately
if those become the intended contribution.

## Review-committee and maintainer perspectives

For a committee: a paper claiming superior fault detection should not be submitted
on this evidence. The transparent negative result improves the artifact's credibility
but does not establish conference novelty. Independent review, external reproduction,
and a clearer research contribution remain open.

For a maintainer: the minimal robustness patch and its regressions remain useful
independently of the comparative result. The formal documentation makes contract and
scope explicit, while CI catches selected drift. The new experiment should not be
presented as proof of production correctness or as a requirement to adopt TLA+.
