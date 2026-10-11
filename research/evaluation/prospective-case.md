# Prospective second-case decision and protocol gate

Status: design prepared; **no second case selected, predictions frozen, or experiment run**.
[Novelty assessment](novelty-review.md) · [Review packet](review-packet.md)

The [active contribution search](scientific-contribution-search.md) now supplies the
candidate-selection question. Its retrospective pilot is not the prospective second
case and does not satisfy this gate. The objective remains scientific contribution.

## Decision now

Defer execution, not preparation. The literature already establishes cancellation
suppression and replay-sensitive upgrades. Repeating those facts in a hand-built
example would add little evidence of a new contribution. The useful next question is
whether a reusable analysis procedure helps another engineer classify a real change
before execution, including where the procedure must abstain.

External review is outstanding. This document is a selection and scoring protocol,
not a preregistered prediction for an unidentified system. Do not call it prospective
validation until the candidate, versions, mappings, and predictions are committed
before any new outcome is observed.

## Candidate selection without selecting on outcomes

Prefer a maintained, independently authored durable-workflow integration with a
public, reproducible test environment and an actual lifecycle/command-affecting change.
Require a license permitting analysis, pinned before/after commits, and an explicit
contract. Reject examples copied from our helper or built to reproduce our known
result. A defect is not required: a compatible change is a valid, useful outcome.

A reviewer should nominate candidates from documented releases or change requests,
record every considered candidate and exclusion, and choose before running replays.
Do not pick the first system in which a failure can be made to occur. If a known
failure motivated selection, disclose that the case is retrospective and cannot
supply the prospective evidence sought here.

| Candidate family | What it could test | Main confound / present decision |
| --- | --- | --- |
| Another Temporal integration with independent lifecycle code | Transfer across application implementations while holding replay engine fixed | Same-engine generality only; eligible if selected without known outcomes |
| Azure Durable Task integration | Whether obligations survive a different versioning mechanism | Requires a new correspondence model and environment; not an automatic reuse of History.tla |
| Synthetic timer/activity cancellation example | Scorer and instrumentation controls | Useful control, ineligible as evidence of independent practical generality |

No repository has been nominated through this protocol yet. Public documentation
inspection during the literature review is not an implementation evaluation.

## Freeze before running

Commit a selection record with repository URL, both source SHAs, dependency locks,
selection rationale, prior knowledge, reviewer identity, and all considered candidates.
Then fix the implementation-to-model mapping and enumerate cases along these axes:

- Cancellation before gate completion, during cleanup, and after command recording.
- Fresh execution versus replay of before/after histories in both directions.
- Relevant migration metadata present versus absent, when supported by the engine.
- A no-cancellation control and a no-command-change control.

Record excluded or unsupported cells explicitly. For each supported cell, predict
accepted permission, invocation outcome, durable command sequence, compatibility,
and effect count or a justified abstention. Specify exactly where the model stops.
A pre-existing effect cannot be scored as undone merely because new execution stops.

## Comparison and scoring

Compare (A) ordinary regression plus documented replay checks with (B) the same checks
plus the explicit obligation/mapping analysis. Freeze both procedures and their
predictions before execution. Use separate reviewers if feasible; otherwise disclose
learning and ordering effects and avoid a causal claim of method superiority.

Record each prediction as correct, incorrect, abstained, or inconclusive. Unknown
infrastructure failure is not compatibility or nondeterminism. Report the full
denominator and every excluded cell, not just a detection count. Retain raw histories,
source hashes, version metadata, effect records, reviewer predictions, and changes
to the model. Any change after seeing results creates a retrospective follow-up;
it cannot repair the original prospective score.

Measure new effort contemporaneously by task, person, elapsed time, and artifact.
Do not invent historical effort for the first case. A second case cannot establish
broad prevalence or universal correctness.

## Falsification and stopping rules

- If the model accepts a prohibited invocation or misclassifies a supported replay
  cell, report that failure and its abstraction cause before revising the mapping.
- If a missing observation requires execution-informed mapping changes, score the
  original attempt inconclusive or wrong as appropriate; disclose the revision.
- If arm B gives no additional useful prediction or diagnosis beyond arm A, retain
  that negative result and narrow the claim to explanation/documentation value.
- If the contract is disputed, request maintainer clarification; do not label the
  implementation defective solely because it conflicts with our preferred contract.
- If no candidate meets the selection criteria, stop broadening the artifact and
  revisit candidate selection and the research hypothesis. Do not substitute a toy
  case or declare the scientific objective achieved. Independent review of existing
  evidence can proceed separately.

The go decision requires a qualifying selection record and explicit predictions,
plus a reviewer judgment that the study addresses a question the literature has not
already answered for us. External review remains a human dependency, not something
another self-run CI job can complete.
