# Cancellation and recovery: measured findings

[Case study](../../RESEARCH.md) · [Protocol v2](cancellation-protocol.md) · [Model](../models/cancellation/README.md) · [Upstream packet](../upstream/caller-cancellation.md)

## Finding and significance

**The cleanup helper can swallow cancellation of its waiting caller and permit an
approved tool to execute.** Accepted approval remains stable, so the earlier decision
safety properties do not detect this defect. The case motivates a separate invocation
obligation: cancellation received during cleanup, before dispatch, prevents dispatch.

Discovery came from source inspection and targeted asyncio execution, followed by a
supported custom-agent Temporal reproducer. TLA+ subsequently formalizes the missing
obligation and produces an abstract counterexample. This is not a model-led discovery,
a demonstrated deployment incident, or a global workflow-cancellation defect.

![Accepted approval and caller cancellation](../figures/cancellation.svg)

**Figure 6.** Approval is retained in both paths. Propagating caller cancellation changes
the invocation outcome and prevents the concrete tool-start event.

## Baseline versus isolated correction

Both variants received identical barrier-controlled stimuli. The proposed correction
also emits exactly one superseded evaluation terminal before propagating live caller
cancellation. It remains isolated; this study does not apply it to production source.

| Child response to the second cancellation | Baseline | Isolated correction | Evaluation terminals, baseline / corrected |
| --- | --- | --- | --- |
| second_raise | dispatched; tool started | cancelled; no tool start | 1 / 1 |
| second_return | dispatched; tool started | cancelled; no tool start | 1 / 1 |

All four caller executions retain approved status. Each variant passed
**23 tests**, including seven asyncio controls and sixteen actual
Temporal executions; **16 completed histories per variant**
replayed without command-compatibility failure. Baseline tests characterize the defect;
their passing does not mean the cancellation contract holds.

Separately, the standalone patch was checked against the original upstream revision:
three cancellation assertions fail and four controls pass before correction; all seven
pass after applying the patch. The packet retains both JUnit records and patch hashes.

| Hypothesis | Measured outcome in both variants | Interpretation |
| --- | --- | --- |
| H1: cleanup outcomes | Nine approval/denial/close × propagation/error/return cases preserve settlement | Selected safety controls hold |
| H2: delayed cleanup | Three settled/closed prefixes remain waiting; release permits completion | Cleanup termination is a progress assumption; a finite wait is not proof of an infinite hang |
| H3: caller cancellation | Two baseline dispatches; two corrected cancellations | Reproduced defect with a concrete tool-start witness |
| H4: replacement and replay | Waiting-state equality after nonsticky worker replacement; final approved dispatch | Graceful replacement with caching disabled, not crash recovery or production sticky routing |
| H5: workflow cancellation | Public workflow cancellation ends as CANCELED | Distinct from cancellation of the handler task |

## Formal results

| Configuration | TLC exit code | Interpretation |
| --- | --- | --- |
| CurrentSafety | 0 | Expected result confirmed |
| CurrentCancellation | 12 | Expected result confirmed |
| CorrectedCancellation | 0 | Expected result confirmed |
| CurrentProgress | 0 | Expected result confirmed |
| BlockedProgress | 13 | Expected result confirmed |
| CorrectedProgress | 0 | Expected result confirmed |

CurrentCancellation violates CallerCancellationRespected (exit 12). BlockedProgress
violates CleanupProgress (exit 13) when cleanup cannot finish. All other checks return
zero. Named diagnostics are required; setup errors are not credited as findings.
The one-call corrected projection preserves the original safety obligations and the
new cancellation invariant. It is not a universal Python refinement proof.

## Provenance and retained evidence

The protocol was published at `ad36441bf60b6a6f51a01bf456fc49366e70aea5` before the Temporal
experiments. Final evidence is from [run 37892391930](https://github.com/charifmahmoudi/temporal-agent-harness/actions/runs/37892391930) at
`3d5bed47d32af5a6c5193bb6857cfa785dc59a4a`. The [machine-readable snapshot](cancellation-results.json)
contains source/model/tool hashes, history hashes, artifact IDs, and observed outcomes.
The exact [implementation archive](cancellation-evidence/implementation.zip) and
[model archive](cancellation-evidence/model.zip) are committed so CI artifact expiry
does not remove the evidence. They retain raw events, full histories, replay results,
JUnit XML, the isolated production diff, configurations, and TLC counterexamples.

`python research/scripts/render_cancellation.py --check` verifies their digests and
the reported outcomes against raw records. The executable reproduction reference is
the [cancellation workflow](../../.github/workflows/cancellation.yml). It prepares an
isolated correction with import/source provenance checks and runs both variants.

## Failed attempts and limits

Runs 37891291257, 37891534941, and 37891860332 failed the worker-replacement query before
recovering usable state. The first also exposed an expected-diagnostic mismatch in the
model runner. Their [protocol amendments](cancellation-protocol.md) explain the eventual
nonsticky procedure. They establish neither recovery correctness nor a recovery defect.
Run 37892043434 passed with a helper-only correction, but review exposed a missing
evaluation terminal. The final patch and assertions close that audit gap.

The result is a reproducible implementation defect and a useful separation of decision
safety, invocation cancellation, audit completeness, and cleanup-dependent progress.
Deployment frequency, arbitrary-call behavior, external-effect rollback, process crashes,
mixed-version replay, and children that suppress cancellation forever remain unmeasured.
Independent review, external reproduction, and research novelty assessment remain open.
