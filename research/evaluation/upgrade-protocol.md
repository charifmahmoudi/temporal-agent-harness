# Cancellation correction: replay compatibility protocol v3

[Case study](../../RESEARCH.md) · [Prior findings](cancellation-results.md)

## Question and frozen inputs

Does the isolated cancellation correction preserve both Temporal command compatibility
and the reconstructed application outcome of previously completed workflows?
This is an offline upgrade experiment, not a live rollout or crash-recovery test.
The source baseline is `c26ec5797f7688307555bb10eec351906ab0c678`.
The input archive is the unchanged v2 implementation evidence, SHA-256
`13da869cfd18ab1e0ecb03a2e7c39290a0e519da870f4e07205be18377b842b7`.
It contains sixteen baseline and sixteen corrected histories. No histories are
selected or discarded based on replay results. The v1 comparison remains unchanged.

## Experiment

Replay all 32 histories under each of the two source variants: 64 cells.
Keep the original workflow definition, converter, SDK lockfile, and recorded inputs.
Use a synchronous terminal observer through the SDK workflow interceptor to copy
application evidence; add no workflow command, await, or changed decision.
Compare reconstructed status, caller outcome, tool-start count, and evaluation
terminal count with the original retained observations where available.
Workflow cancellation has only a retained server terminal and a pre-cancel snapshot;
do not invent an application-outcome oracle for that scenario.

| Obligation | Control / measurement |
| --- | --- |
| Input integrity | Verify archive, history, workflow-definition and implementation hashes |
| Same-version validity | All 32 original-version replays must succeed; all available outcome projections must match |
| Upgrade compatibility | Baseline histories replayed under corrected source |
| Reverse compatibility | Corrected histories replayed under baseline source; diagnostic, not a rollback recommendation |
| Command versus semantic agreement | Report replay result and application comparison as separate fields |
| Observer sensitivity | Deliberately alter a retained expected outcome; the comparator must reject it |

## Scoring fixed before execution

Report each cell as command-compatible, nondeterministic, or experiment-error.
Only the SDK's explicit nondeterminism exception is evidence of command mismatch;
timeouts, setup errors, and missing observer state are not successful detections.
For compatible replays with an available original outcome, independently report
application match or mismatch. A mismatch is a changed reconstruction, not proof
that a historical external effect was repeated or undone. The probe has no external
side effect. An absent oracle is reported as unavailable.

Same-version disagreement invalidates the corresponding cross-version interpretation
until investigated. Expected cross-version outcomes are not assumed. Retain all
cell records, runtime/source hashes, errors, and original projections before
asserting acceptance. Run with isolated imports for both variants. CI should fail
on experiment errors and invalid same-version controls, but a measured upgrade
incompatibility is a reportable result, not an infrastructure failure.

## Interpretation and stopping rule

If command replay fails, the patch is not shown safe for those histories without
an explicit versioning/routing strategy. If replay passes but application outcomes
change, replay success alone is insufficient for the stronger application claim.
If both agree, report only compatibility for these selected completed histories.
Do not infer arbitrary-history, in-flight upgrade, production sticky routing, or
cross-framework guarantees. Versioning changes require a separate experiment.

Complete this milestone when all cells are reported, controls pass, and documentation
states the result and deployment implications without altering v2's historical claims.
Independent review and maintainer feedback remain external gates.

## Observer-control amendment

The first local pilot completed all 64 cells: same-version observations matched,
while both caller-cancellation scenarios changed application outcome across versions
despite successful command replay. Before the final measured run, add a paired replay
without the observer for every cell. Require equal command classification in every
pair. This checks one possible instrumentation explanation; it does not prove full
observer noninterference. Also freeze workflow and dependency-lock hashes and test
timeout/error classification separately. Report 64 matrix cells and 128 replay
executions, rather than counting the ablation as additional independent histories.
