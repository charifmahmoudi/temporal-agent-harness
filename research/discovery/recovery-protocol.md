# Exploratory recovery probe, version 1

Published before probe execution, 2026-10-10. Candidate C1 in [candidates](candidates.md).
Purpose: validate a small operational comparison and test whether anything remains
unexplained by existing contracts. This is exploratory, not a held-out evaluation.

## Subjects and environment

GitHub Actions Ubuntu, Python 3.12. Temporal Python 1.34.0, Temporal CLI 1.7.0
(archive SHA256 8b5de72e622f4ae062d0d5d948ca398de6212d63b2f25766a1cb810a3dc2d0ed).
Restate Python SDK 1.0.5, server 1.7.13 (Linux musl archive SHA256
5429b216b68f3fa52b7f0e6627a2c2a86fc0c75d19b1e152cd2e7dcd8bab4c82).
Record dependency freeze, executable versions, source hashes, CI revision, histories,
HTTP responses, service/server logs, and per-invocation side-effect ledger.
No local executable probes or tests.

## Design

Two independently implemented engines, three arms, three fresh workflow IDs per arm
(18 planned trials). Repetitions assess execution stability, not independent bugs or
production prevalence. Sequential order: compatible cancel, broken cancel/restore,
broken force-stop, repeated three times per engine. No latency comparison across CI
machines. No nested calls, external transactions, real money, or irreversible effects.

Original workflow runs one durable effect that appends a local ledger entry, then
waits durably. Establish the wait through engine-visible history/status. Stop its
worker/endpoint; cold resume prevents a cached execution hiding the changed code.
For broken arms, replace the first recorded operation with a different command
(activity/run becomes timer/sleep). This is an intentionally incompatible deployment,
not a recommended upgrade path. Verify a typed nondeterminism error before intervention.

| Arm | Intervention | Recorded outcomes | Contract-informed prediction |
| --- | --- | --- | --- |
| Compatible cancel | Resume original code, request cancellation | API acknowledgement, terminal status, cleanup ledger | Cooperative cancellation completes and cleanup runs. |
| Broken cancel/restore | Resume incompatible code, request cancel, observe 12 seconds; restore original code | Typed mismatch, acknowledgement, status and cleanup before/after restore | Accepted cancel remains unable to complete while mismatch persists; restored code permits cleanup and closure. |
| Broken force-stop | Resume incompatible code, terminate (Temporal) / kill (Restate) | Typed mismatch, acknowledgement, terminal status, cleanup ledger | Engine closes execution without workflow compensation. |

Poll preconditions and terminal states with a 60-second bound. Bounded noncompletion
does not prove indefinite failure. Use engine-specific status/errors; do not equate
Restate terminal failure with Temporal canceled solely by label. A replay mismatch
must be observed before attributing any blocked progress to incompatibility.
Only cleanup effects recorded by the durable effect API count as compensation.
API success alone never counts as cancellation completion. Restoring code is the
within-invocation causal control; restart transport failures remain distinguishable.

## Interpretation and failures

Implementation clarification before first execution: Restate uses a durable promise
as its wait barrier (persisted GetPromise journal command), pauses the invocation,
restarts the same endpoint URI, and resumes it. Pause/resume is applied to compatible
and broken arms alike. Temporal uses a no-op signal to schedule a new workflow task
after the cold worker change. Neither wake action releases the workflow's wait.
Restate's new deployment registration is not used to bypass normal version pinning;
the incompatible endpoint replacement is deliberate fault injection.

Setup failures, missing barriers, unsupported API calls, or missing mismatch evidence
are inconclusive. Preserve them and label any driver corrections before rerunning.
Do not silently change the planned arms or reclassify timeouts as confirmed defects.
A different observed result triggers inspection of history and contract, not an
automatic bug claim. Exact agreement supports only a small known-contract comparison.
It does not establish a novel contribution, broad representativeness, an impossibility
theorem, or advantage over ordinary operational documentation.

Expansion requires an unanswered consequential question: e.g., existing recovery
guidance demonstrably leads operators to worse decisions on independently sampled
incidents. That would need a separate prospective evaluation and suitable participants;
we will not infer it from this synthetic probe.
