# Continuation baseline and activation diagnosis

Recorded 2026-10-10 after inspecting the first 24 Nexus context trials, before
implementing or running this follow-up. All cells are development cases. No
uninspected case is represented as a holdout.

## Question

The affected default-cache execution records a successful Nexus completion,
starts and fires a timer, then fails its next task. This precedes offline replay.
Does a conventional, bounded continuation sweep expose the defect without an
explicit recovery operation? Is its first failure a live or replay activation?

Use the same two adjacent SDK revisions, shared dependency lock, Rust 1.94.0,
and checksum-verified Temporal CLI 1.7.0 / server 1.31.0 as the
[initial protocol](open-recovery-protocol.md). Preserve that experiment unchanged.

## Frozen test grammar

After the upstream successful async Nexus result, use each legal suffix:

| Suffix | Purpose |
|---|---|
| `return` | Immediate termination, existing regression shape |
| `state` | Read/assert existing workflow state synchronously, then return |
| `timer0` | Await a zero-duration SDK timer, then return |
| `timer1` | Await a one-second SDK timer, then return |

Run all four suffixes under default cache and cache disabled, on both SDK
revisions, three repetitions: 48 executions. The sweep enumerates this grammar;
it is an ordinary exhaustive baseline, not a proposed novel generator. It derives
fixtures and test wrappers from the upstream source but the legal grammar and
payload oracle are supplied by us. It does not derive them from arbitrary programs.

Print the activation run ID, replay flag, and eviction flag before checking the
SDK's accumulated wake flag. Print a matching failure marker at that check, and
workflow-side markers before/after the result and continuation. Match diagnosis
by run ID; backing-workflow activations must not be mistaken for caller activations.
Instrumentation is diagnostic and can affect timing. The uninstrumented first
experiment is the detection control; do not overwrite it or infer timing superiority.

## Predictions, scoring, and stopping

Predict affected `return` and `state` pass; `timer1` fails in both cache treatments;
all fixed cells pass. `timer0` is unresolved: inspect whether it actually creates a
later activation. A zero timer is not assumed to be a synchronous operation.

The existing payload assertion must pass for successful cells. Require actual
Nexus completion, workflow completion, clean task history, and completed-history
replay. Confirm TMPRL1100 only from an individual recorded task failure after the
operation completion, or an explicitly identified offline replay error. Preserve
other outcomes as inconclusive. A 20-second live alarm is not proof of deadlock.
Retain raw logs, histories, fixture and diagnostic patches, lockfile, source
revisions, hashes, and server information. Verify retained evidence independently
of the CI exit status; the initial experiment's workflow succeeded even when
expected affected fixtures failed.

If the first cached failure has `replay=false`, reject restart/reconstruction as a
necessary cause for this fixture. If the ordinary suffix sweep exposes the same
distinction, it supplies an adequate development baseline; no superiority is claimed.
If it does not, diagnose the instrumentation or fixture before inventing an analyzer.

This experiment cannot establish general test reduction, coverage beyond this
grammar, crash recovery equivalence, or scientific novelty. Do not expand selection
heuristics until a second mechanism and a concrete baseline limitation are established.

## Execution status

The [48-cell comparison](continuation-results.md) is now complete. No predictions
or grammar choices above were rewritten. Both affected timers fail; return/state
controls and all fixed cells pass. Cached first failures precede replay/eviction.
