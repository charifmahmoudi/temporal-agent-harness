# Activity-backed cancellation and upgrade — protocol v4

[Case study](../../RESEARCH.md) · [Prior replay experiment](upgrade-results.md)

## Question and contract

Does the caller-cancellation defect permit an actual Temporal activity to run, and
can its correction be introduced without breaking previously recorded activity
commands? The study baseline is `de0d3d30f94f2357770080fcc848850962e76d4a`.
This protocol is committed before execution. v1–v3 results remain unchanged.

The proposed contract is narrow: cancellation delivered to the waiting caller during
evaluator cleanup, before activity scheduling, must prevent that invocation from
scheduling the activity. Accepted approval need not be revoked. Cancellation after
an activity was scheduled is outside this contract; no rollback is promised.

## Variants and controlled effect

* **B:** unchanged baseline helper, which can swallow caller cancellation.
* **C:** the existing isolated correction, which propagates outstanding cancellation.
* **V:** the same correction guarded by a Temporal patch marker at the changed
  cancellation branch. Old history without the marker takes the legacy branch during
  replay; new execution at that branch takes the correction. This is a study variant,
  not a production rollout recommendation or a new versioning technique.

Use the harness's public activity-tool decorator. The activity appends a JSON record
to a test-only ledger outside workflow memory and fsyncs it. Record activity attempt,
workflow identity, activity identity, worker source hash, and case ID. Disable retries
for the probe to simplify attribution; do not infer exactly-once delivery in general.
Compare server history (scheduled/started/completed activity events) with that ledger.

## Experiment matrix

| Arm | Declared cases | Measurements |
| --- | --- | --- |
| Fresh execution | B/C/V × approval, denial, caller cancellation with child re-raise, caller cancellation with child return | Outcome, stable decision, evaluation terminal, scheduled activity, ledger effect |
| Offline replay | All 12 fresh histories under B/C/V: 36 cells | SDK command compatibility; explicit nondeterminism versus experiment error |
| Live worker replacement | B → C/V × both child responses × before caller cancellation / after activity completion | Recovery, new dispatch, explicit nondeterminism, ledger delta |

Before-cancellation replacement stops B after cleanup entry, reconstructs with C/V,
then delivers cancellation as a new input. After-completion replacement stops B once
the activity has completed but the agent session remains open; the new worker must
replay the command-bearing prefix. A checkpoint signal drives a workflow task after
replacement. Both workers disable workflow caching and use separate processes/imports.
This is graceful nonsticky replacement, not a crash, production routing, or concurrent
mixed-version rollout experiment.

## Scoring and controls fixed before execution

Record raw history, queries, worker logs, ledger entries, and import/source hashes
before assertions. Every fresh history must replay under its own source variant.
Approval/denial controls establish normal activity dispatch and rejection. Both child
responses must be exercised; do not substitute a workflow-local tool-start event for
an activity effect. Require delivered-cancellation evidence and scheduled-event order.

For cross-version replay, report all cells, whether compatible or nondeterministic;
do not pre-score an anticipated result as a detection. Only an SDK nondeterminism
exception or explicit server WorkflowTaskFailed nondeterminism cause is a command
incompatibility. Timeouts, process failures, missing histories, and setup errors are
experiment errors and fail CI. Preserve partial evidence on those paths.

The intended remedy criterion is: V replays baseline command-bearing histories and
prevents fresh or newly delivered pre-dispatch cancellation from scheduling an activity.
For after-completion replacement, no additional ledger entry should appear, but the
existing entry must remain. Replay cannot reverse that old effect. C's cross-version
outcomes are measured, not assumed. Do not classify incompatibility caused by the
intentional behavioral change as a new Temporal defect.

## Formal obligation and claim boundary

For an invocation i, let D(i) mean caller cancellation was delivered while cleanup
was awaited, S(i) mean an activity command was scheduled, and E(i) mean the probe's
ledger effect occurred. For new corrected execution the target is D(i) ⇒ ¬S(i).
An activity schedule is a durable commitment boundary distinct from accepted approval;
absence of a ledger entry alone is insufficient to establish absence of scheduling.

For historical replay, the obligation is command compatibility with the accepted
history. A versioned remedy may intentionally preserve a historical violation of the
new cancellation contract. Report that tradeoff explicitly; never claim retroactive
enforcement. The existing Cleanup model remains an invocation abstraction, not a
model of Temporal history matching or activity delivery.

The local test server failed startup before this experiment. CI will execute the live
arms. A successful result requires every planned case accounted for, valid controls,
retained evidence, a clear mechanism, and synchronized maintainer/scientific assessment.
Independent review, deployment incidence, generality, and novelty remain open.
