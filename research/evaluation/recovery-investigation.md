# Independent recovery investigation: reproduced development case

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

## First measured result — 2026-10-10

[CI run 38030115380](https://github.com/charifmahmoudi/temporal-agent-harness/actions/runs/38030115380)
executed the prediction committed in `5e4ee16c45f2da712f0d4824f57daadc369e02d0`.
Both arms used Python 3.12.15. The [retained evidence](recovery-673-evidence.json)
contains the complete summaries and six losslessly compressed histories, each with
its SHA-256 digest. This retains evidence beyond CI artifact expiration.

| SDK | Live executions satisfying precondition | Typed replay nondeterminism | Successful replay |
|---|---:|---:|---:|
| 1.8.0 | 3/3 | 3/3 | 0/3 |
| 1.9.0 | 3/3 | 0/3 | 3/3 |

All affected failures report an update state-machine mismatch at the second activity
schedule. The affected histories have that schedule at event 20, 20, and 17; the
variation confirms that event numbers alone should not define a scenario. There
were no infrastructure or collection errors in CI. These are six executions of one
known defect family, not six discoveries. Release and server provenance limitations
above still apply. We have reproduced an external report; we have not independently
validated a new testing method.

## Next discriminating experiment

The upstream fix already adds `replay_with_signal_and_update_same_task` and
`update_after_empty_wft` regressions. Our adapter currently adds retained evidence
and release comparison, but demonstrates no detection advantage over those tests.
The research question is therefore: **can a causal boundary coverage strategy expose
live/replay divergence more efficiently or more broadly than existing regression
selection and seeded random scheduling under the same execution budget?**

Before implementing that strategy:

1. Pin and record a shared test-server executable and SDK dependencies. Replay the
   same retained histories under both releases to remove history-generation differences
   from that comparison. A single-Core-patch experiment remains a separate control.
2. Define scenarios by observable causal relations: signal delivery, first activity
   completion, update acceptance, timer firing, and workflow-task boundaries. Use
   real executions to obtain histories; do not fabricate impossible event orders.
3. Give systematic and random selection the same scenario grammar, oracle, and
   execution budget. Include upstream regressions as a strong baseline, report
   invalid/inconclusive trials, and charge setup and minimization costs explicitly.
4. Freeze that protocol before collecting comparative outcomes. Use this case for
   development only; reserve previously uninspected cases for evaluation.

A candidate contribution would require evidence that the coverage criterion or
minimization method adds something existing techniques do not already supply.
If comparable baselines obtain the same coverage and detection results, reject the
candidate. Do not rename reproduction as scientific novelty.
