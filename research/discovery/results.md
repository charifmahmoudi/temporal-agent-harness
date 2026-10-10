# Bounded discovery: results and decision

2026-10-10. **No strong new scientific finding established.** The process produced
a corrected issue screen and a reproducible two-engine comparison of known recovery
semantics. We reject a novelty claim for the observed cancellation/termination
distinction. This is a useful public evidence note, not a demonstrated new method,
new failure mechanism, or prevalence study.

## Five-step ledger

| Step | Deliverable | Status |
| --- | --- | --- |
| 1. Independent evidence | [Scope](protocol.md), [43-issue inventory](inventory.md), [raw screen](screen.json) across Temporal, DBOS, Restate | Complete within stated bounds; keyword and earliest-result bias retained |
| 2. Candidate questions | [Three assessed candidates](candidates.md), nearest answers, falsifiers, exclusions | Complete; two rejected before unnecessary experiments |
| 3. Exploratory probes | [Prospective protocol](recovery-protocol.md), 18 trials in two independent engines | Complete; all planned arms executed, no failed setups or driver reruns in the initial run |
| 4. Claim decision | Results below and [conditional decisive evaluation](evaluation-gate.md) | Reject novelty for these observations; larger empirical claim remains unsupported |
| 5. External challenge | [Public review packet and request #3](https://github.com/charifmahmoudi/temporal-agent-harness/issues/3) | Published before completion of the probe; substantive independent feedback pending |

## Executed evidence

[GitHub CI run 38059968219](https://github.com/charifmahmoudi/temporal-agent-harness/actions/runs/38059968219)
passed both engines at branch revision `b0ad71ce2fd1025cc04e38ff52440c5fb672fa9f`.
The original protocol was published at `1e0ef1ed36ce4d06e0e7b320fd7a68d86a9a5421`;
implementation clarifications preceded execution. Checkout merge revisions are retained
inside the raw summaries. All execution happened in GitHub Actions.

| Arm, three repetitions per engine | Temporal 1.34.0 / CLI 1.7.0 | Restate SDK 1.0.5 / server 1.7.13 |
| --- | --- | --- |
| Compatible cancellation | 3/3 canceled; one cleanup each | 3/3 completed with `[409] cancelled`; one cleanup each |
| Broken replay, cancel, restore original code | 3/3 typed mismatches before cancel; still running without cleanup after 12-second wait; canceled with one cleanup after restore | 3/3 RT0016 mismatches before cancel; still backing off without cleanup after 12-second wait; canceled with one cleanup after restore |
| Broken replay, forced stop | 3/3 terminated; no cleanup | 3/3 completed with `[409] killed`; no cleanup |

Every trial recorded the initial effect exactly once in this execution. This does not
establish an exactly-once external-effect guarantee under crashes or retries. Request
acceptance was observed separately from terminal state. The broken cancel arm was
bounded, not a proof that cancellation could never finish. Restoration also restarts
the endpoint/worker; the pre-intervention typed mismatch and compatible restart arm
help separate this from simple unavailability, but do not characterize every outage.

There are 18 executions of one synthetic workflow family, not 18 independent defects.
The two engines implement their own contracts, and terminal labels are not treated
as interchangeable. These are deliberate incompatible deployments, not normal safe
rollouts. No production workload, nested compensation, distributed transaction, or
multi-node failure model was evaluated. DBOS contributed discovery evidence, not a
third execution subject.

## Retained artifacts and verification

The exact CI ZIP artifacts are retained as base64 so GitHub artifact expiration will
not erase the evidence: [Temporal archive](evidence-temporal.zip.b64),
[Restate archive](evidence-restate.zip.b64). Decode base64 to recover the original ZIP.
Each contains dependency freeze, source hashes, server version/logs, ledger, and raw
history or HTTP/journal records. The summaries alone are not the evidence oracle.

| Artifact | GitHub artifact ID | SHA256 of decoded ZIP |
| --- | --- | --- |
| Temporal | 11672747891 | `3639897379f0a03897d3f354f1d418fa5428707e2feb475c8421633c56eb1b39` |
| Restate | 11673005872 | `eb4c2bc237801598e54224e726052c16d9985eeb1e535d6b788a6bfa13aa65d0` |

[Separate auditor](../scripts/audit_discovery_recovery.py) checks artifact digests,
planned-cell completeness, ledger/history agreement, typed failure before intervention,
and actual terminal evidence. It does not use the probe's `matches_prediction` flags
as its verdict. Temporal's intermediate describe status is retained in the summary;
final history independently shows a further mismatch after the cancellation request.
Restate's timed intermediate state is also checked against the HTTP transcript.
The audit is run by the Bounded research discovery workflow. Its
[first run](https://github.com/charifmahmoudi/temporal-agent-harness/actions/runs/38060319730)
failed because the new checker incorrectly required HTTP 200 for every Restate
control acknowledgement. The retained transcript shows cancellation returns 202
Accepted and kill returns 200. The original probe correctly accepted successful
HTTP responses and separately checked completion. The audit correction accepts 2xx,
cross-checks the recorded acknowledgement status, and preserves all terminal-state
requirements. No probe code, outcome, or raw evidence was changed. Corrected audit
execution is pending at this update; the first failed audit remains visible.

One diagnostic wording limitation: Restate's mismatch message labels sleep as the
previous command and run as the current command, whereas the retained original
journal contains Run and the injected code attempts Sleep. We use the typed RT0016,
the raw journal, and source for classification; this wording observation is not a new
defect claim and was not used to reinterpret the planned outcomes.

## Scientific decision and next action

The outcome is predicted by [Temporal cancellation/termination documentation](https://docs.temporal.io/develop/python/workflows/cancellation)
and [Restate's invocation contract](https://docs.restate.dev/services/invocation/managing-invocations),
with Restate's incompatibility limitation already explained in [issue #3656](https://github.com/restatedev/restate/issues/3656#issuecomment-3227324174).
The [nearest-work assessment](candidates.md) also overlaps the established cancellation
literature. Agreement with these sources does not create novelty.

The next justified action is independent challenge of a specific missing operator
decision problem, not a larger synthetic sweep. [Evaluation gates](evaluation-gate.md)
define what would make a future empirical contribution credible, its primary outcome,
strong documentation baseline, independent sampling, and rejection conditions.
No advantage, incident frequency, or general recovery theorem is asserted now.
