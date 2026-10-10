# Recovery mechanisms: what the current experiments cannot observe

## Decision

Investigate **automatic selection of recovery points and post-recovery operations
for still-running workflows**. The immediate problem is to expose states missed
by completed-history replay, while checking result identity and bounded progress
as well as replay exceptions. This is a candidate research problem, not a novel
algorithm or an established literature gap.

Do not extend the delay-order heuristic. Its negative result stands. The evidence
below changes the unit of investigation from a delay pair to a reachable workflow
prefix, a recovery operation, and an executable continuation.

## What was actually checked

On 2026-10-10, we inspected primary issue reports, linked patches, and testing
literature. At that inspection only the #673 family had been reproduced by this project.
The later [Nexus context experiment](open-recovery-results.md) now supplies measured
evidence; its live continuation failures narrow the recovery-specific interpretation. The other
rows are source-supported development cases, not our experimental results. Reading
them excludes them from a future blind holdout set. This is a purposive mechanism
comparison, not a systematic prevalence study or exhaustive literature review.

An audit of the retained [pilot evidence](recovery-comparison-evidence.json) found
**72 completed histories and zero open histories**. Each runner waits for the live
workflow result before replay. The [classifier](../scripts/reproduce_recovery_673.py)
counts only typed `NondeterminismError`; other replay exceptions are inconclusive.
That conservative rule was appropriate for #673, but is not a complete recovery
oracle. It does not falsely mark these other exceptions as successful replay.

## Distinct mechanisms and required observations

| Case | Failure mechanism | State or operation needed | Relevant observation | Evidence status |
|---|---|---|---|---|
| Temporal Python [#673](https://github.com/temporalio/sdk-python/issues/673), Core [#833](https://github.com/temporalio/sdk-rust/pull/833) | Update delivery crosses an activity-completion boundary during reconstruction | Signal, completion, update; replay resulting history | Required activity schedule versus reconstructed commands | Reproduced here; typed nondeterminism |
| Temporal Python [#1881](https://github.com/temporalio/sdk-python/issues/1881), Core [#1616](https://github.com/temporalio/sdk-rust/pull/1616) | Regrouping local-activity resolutions changes which activity owns a sequence number | Fan-out, first-completion wait, conditional follow-up activity | Result-to-handle identity; reported decoding failure | 12 live/replay trials; affected local decoding signature, remote/fixed controls pass (see local-activity results) |
| Rust SDK [#1353](https://github.com/temporalio/sdk-rust/pull/1353) | Internal shared-future wake is classified as a non-SDK wake during replay | Await Nexus result, remain open, then query/evict/restart | Recovery/query success and ability to continue | 24 matched executions; timer continuation exposes live task failure before offline replay (see results) |
| DBOS Python [#358](https://github.com/dbos-inc/dbos-transact-py/pull/358) | Database error leaves process-local receive coordination uncleared | Disconnect during receive and subsequently recover | Recorded notification is eventually consumed under restored service | Fix patch and developer account inspected; not reproduced here |

For #1881, the reported symptom is a bool/string conversion failure, not demonstrated
silent corruption. A same-type wrong-result variant is a hypothesis only. The fix adds
an activation index to new local-activity markers and preserves legacy behavior for
old markers; a fixed SDK must therefore be tested on freshly recorded fixed histories,
not assumed to repair every historical input. Merge: `e163abd6dc19040064986a63c8b8cf4756ffd320`.

For #1353, the patch wraps polling of the shared result future in `SdkGuardedFuture`.
Its description contrasts still-running recovery with existing completed-workflow
tests. The inspected diff contains the guard and changelog, not a new regression test.
The description includes downstream validation claims and an AI-assistance disclosure;
we treat it as a reproduction lead, not independently confirmed behavior. Merge:
`d936c6cc6455256417c917c3637d52e53acb8178`.

For DBOS #358, the diff moves coordination cleanup into `finally` and increases the
chaos workload size. The developer [account](https://www.dbos.dev/blog/how-to-test-durable-execution)
connects the stale condition variable to a receive that remains blocked after a
database error. This requires a real database/fault path, not just a Temporal replay
adapter. Merge: `6656a55a5ac57a4c62bcd3ba76d8b65792323b47`.

## Three limitations supported by this comparison

1. **Completion hides some recovery states.** Our corpus cannot support claims about
   replay while a workflow remains open. #1353 supplies a concrete lead to test this
   distinction. This is a limitation of the exercised scenarios, not proof that the
   replay API cannot handle partial histories.
2. **An exception class is not a correctness contract.** A known runtime defect can
   surface as decoding failure; a recovered process can also remain blocked. Raising
   every exception to a confirmed defect would introduce false positives. Preserve
   raw failures, then confirm semantic mismatches with controls and trace evidence.
3. **One recovery operation does not represent all others.** Offline replay, cache
   eviction, process restart, and a database disconnection retain different volatile
   state and execute different recovery paths. They must be separate treatments.

The shared issue is the test's observation boundary: which live state it reaches,
what it destroys, and what it requires to work afterward. This is our inference
from the cases. It is not a theorem that these defects share one implementation cause.

## Prior work prevents several easy novelty claims

| Existing work | Capability already available | Consequence for a contribution claim |
|---|---|---|
| [Durable Functions semantics, OOPSLA 2021](https://www.microsoft.com/en-us/research/wp-content/uploads/2021/10/DF-Semantics-Final.pdf), §6.3 | Equivalence between replay and the underlying execution model | Live/recovered observational equivalence is not new |
| [CrashMonkey/ACE, OSDI 2018](https://www.usenix.org/system/files/osdi18-mohan.pdf), §5.1 | Tests recovered data and performs writes to expose unusable recovered objects | Executing operations after recovery is not new |
| [Coyote specifications](https://github.com/microsoft/coyote/blob/main/docs/concepts/specifications.md) | Safety and progress monitors; bounded heuristics for liveness | Adding progress checks is not new, and a timeout is not an infinite-trace proof |
| [Nekara, ASE 2021](https://www.microsoft.com/en-us/research/wp-content/uploads/2021/09/nekara-ase2021.pdf) | Models concurrency APIs for systematic testing across platforms | Exposing SDK scheduling hooks is not itself new |
| [DistFuzz, NDSS 2025 artifact](https://github.com/zouyonghao/DistFuzz) | Request/fault/timing inputs, message-sequence feedback, record/replay | More timing dimensions and feedback alone do not establish novelty |
| [Resonate testing guidance](https://www.distributed-async-await.io/sdk/testing-against-the-spec) | Invariants, seeded fault simulation, differential comparison with shipped behavior | Combining these established checks is a baseline, not a new scientific method |

These sources establish relevant capabilities, not measured performance on our
workflow cases. We have not run these tools against this corpus and cannot claim
they miss these bugs. Generic systematic testing can express these scenarios when
a developer supplies the appropriate operations, hooks, and assertions.

## Precise candidate problem

Given a workflow program, its SDK event interface, and reachable execution traces,
**derive a small set of recovery points and follow-up operations that distinguish
incorrect reconstructed states from the corresponding uninterrupted execution**,
without hand-writing a different recovery scenario for each known defect.

A test consists of `(reachable prefix, recovery treatment, legal continuation,
observations)`. Observations include logical result identity and enabled operations,
not merely event counts. The reference and recovered runs must share relevant inputs
and activity outcomes. Equality of arbitrary wall-clock timings is not required.
Legitimate retries and allowed ordering differences must be accounted for explicitly.
Do not invent histories or call a timeout a proof of deadlock.

The possible contribution is a derivation/reduction method with a stated preservation
argument and empirical savings over strong selection baselines. Neither has been
constructed. A hand-written continuation for #1353 would establish a reproducer,
not this contribution. Automatically choosing fewer tests also needs evidence that
it preserves distinctions relevant to the declared fault model.

## Next experiment and stop conditions

First reproduce #1353 on pinned affected/fixed Rust SDK revisions with a compatible
Nexus-capable server. Use the same workload prefix in two contexts: terminate after
the result, or remain open awaiting a later input. For the open context, compare
no recovery, offline replay of a valid fetched prefix, cache eviction, and worker
restart; query state and deliver a continuation input. Retain complete traces and
outputs. A failed setup or unsupported recovery operation is inconclusive.

Before execution, freeze the exact revision/server pair, commands, cut conditions,
number of repetitions, and bounded progress threshold. The source report suggests
a distinction; it does not justify assuming which of these cells will fail.

- If the affected behavior cannot be reproduced, stop treating this report as
  experimental evidence and diagnose the environment or narrow the claim.
- If completed-history tests expose the same defect under matched conditions, reject
  the claimed missed context for this reproducer.
- If the context distinction is reproduced, add the local-activity identity case as
  a separate development mechanism; do not count timing variants as new mechanisms.
- Only then compare a proposed selection method with all reachable bounded cuts,
  uniform random cuts, and hand-written regressions using identical continuations
  and semantic oracles. This separates selection quality from a stronger oracle.
- If ordinary dependency analysis or existing systematic exploration gives the same
  result at comparable cost, reject the novelty claim. Reserve uninspected cases
  before tuning; none of the four cases above is a blind holdout.

**Current status:** the [24-cell Nexus experiment](open-recovery-results.md) establishes
a continuation-sensitive missed context, including failures under default caching.
It does not establish restart as a necessary cause. The [48-cell suffix baseline](continuation-results.md) now
detects the Nexus defect before any cached caller replay or eviction, and [local-activity identity](local-activity-results.md) is a
separately reproduced development mechanism caught by immediate replay. A new method, independent validation, and novelty
remain unestablished.
