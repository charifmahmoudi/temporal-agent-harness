# Independent recovery investigation: development case selection

## Problem and limits

Test whether unchanged workflow code produces different relevant behavior in live
execution and reconstruction. This investigation starts with an independently reported
defect, not another extension of our approval example. The first case is **development
evidence only**: its issue and fix have been read, so it cannot be a held-out evaluation.
No testing-method novelty or baseline superiority has been established.

Selected report: [Temporal Python #673](https://github.com/temporalio/sdk-python/issues/673),
overlapping signal/activity completion and update processing. The report describes
an update seeing stale running state on replay and omitting a required activity.
The linked [Core fix #833](https://github.com/temporalio/sdk-rust/pull/833) changes
handling of empty workflow-task sequences and update sequencing. It already includes
unit and integration regressions. Rediscovering its scenario is not a contribution.

## Version provenance

| Arm | Python SDK tag / tree | Bundled Core commit | Relationship to fix |
|---|---|---|---|
| Reported affected | `1.8.0` / `b16215104069f798b79592679d8a16dd3d702883` | `9690510f46b95f226b100871708e3212304f04d1` | Does not descend from fix merge |
| Expected fixed | `1.9.0` / `3901cb708025296c5aed35ea28550501d3f08899` | `bba9fe14958f66dab4412015cdf46d3c1c28897d` | Descends from fix merge |

Fix merge: `592187b4d1590a4361072799d94242af51b4c14b` (2024-10-23).
GitHub tree/submodule and commit comparisons were inspected. The affected Core commit
diverges from the merge (6 ahead, 20 behind); the fixed commit is 17 commits ahead,
zero behind. This is a release-level control, not an isolated causal ablation of #833.

## Recorded development prediction and execution plan

Before CI execution, predict: adapted live executions complete two activities under
both SDKs; replay of each affected-version history reports a typed nondeterminism
failure under 1.8.0, while each 1.9.0 history replays successfully under 1.9.0.
Use three signal-to-update delays (0.1, 0.5, 1.0 seconds), with a three-second workflow
timer. These are three timing probes of one known case, not independent bugs.

The [runner](../scripts/reproduce_recovery_673.py) is an independently written adaptation:
it uses a counter and completion count, a signal starting an activity, and an update
that declines work when the counter is nonzero. It extends the timer to three seconds,
retains results and full histories, and uses the unsandboxed workflow runner consistently
in both arms. It does not test sandbox behavior or reproduce the issue byte-for-byte.

Each arm uses an isolated SDK installation and the SDK's default time-skipping server.
This first gate does not pin a shared server binary, so cross-release observations
must not be attributed solely to the Core change. Server/environment controls must
be tightened before a comparative performance or causal study.

Scoring: live update must accept work, workflow result must be two completions, and
server history must contain two schedules and two completions. Otherwise the trial
is inconclusive. Only `workflow.NondeterminismError` counts as a replay defect; other
exceptions and infrastructure failures remain inconclusive. Unexpected predictions
fail CI after saving observations. No timeouts are scored as nondeterminism.

## Initial environment finding

Both SDK versions installed locally. Test-server startup for 1.8.0 failed while trying
to contact `temporal.download`, before a workflow ran. This is infrastructure failure,
not a reproduction or refutation. The dedicated
[CI workflow](../../.github/workflows/recovery-reproduction.yml) runs the two isolated
arms and retains JSON histories, hashes, and typed errors. Results are pending at
the time this protocol is first committed.

## Gate before building a generator

1. Obtain affected/fixed reproduction with sufficient environmental provenance.
2. Compare the adapter with the already published upstream regressions. State what
   information or scenario selection a proposed generator would add.
3. Freeze a causally valid scenario grammar and equal execution budgets for systematic
   and seeded-random generation. Do not mutate histories arbitrarily into impossible
   event sequences or infer bugs from expected command mismatches.
4. Compare coverage and time-to-detection on multiple known development cases. Keep
   worker-cache eviction, history pagination, event grouping, and process crashes
   distinct until their legal transformations are specified.
5. Select independent evaluation cases before reading their fixes or adapting the
   generator. Issues #1591 and Core #1616 have already been inspected and are not
   eligible as blind holdouts. A later chronological cohort may be necessary.

Relevant baselines include the upstream regression tests, deterministic simulation
and differential conformance testing described by
[Resonate](https://www.distributed-async-await.io/sdk/testing-against-the-spec), and
[Durable Functions' formal replay semantics](https://angelhof.github.io/files/papers/durable-functions-2021-oopsla.pdf).
This round must demonstrate an actual gap against those techniques before proposing
a new method. A passing reproduction alone only establishes an executable starting point.
