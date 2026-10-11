# Claim-by-claim novelty assessment

Review date: 2026-10-09. Subject: `ccb74997404f6b9fd9f5654ac5a441337581d673`.
[Storyline](../storyline.md) · [Earlier related-work review](../related-work.md) · [Independent review packet](review-packet.md)

## Current research direction

The owner has chosen to pursue a scientific contribution and rejected an
experience-report reframing. [Search iteration 1](scientific-contribution-search.md)
adds live synthesis, execution-edit checking, and partial-observation control to the
closest-work comparison. It rejects the broad update-synthesis novelty claim and
retains source-derived replay/observation analysis as an unestablished candidate.
The assessment below concerns what the earlier evidence supports, not a decision
to lower or replace the scientific objective.

## Decision

The present evidence supports a focused engineering case study. It does not support
claiming a new trace-validation method, a new versioning method, or the discovery
that workflow upgrades can invalidate execution history. The strongest contribution
candidate is the documented cancellation defect and the connected evaluation of its
contract, repair, and history-cohort limits. Scientific novelty remains unestablished.

This assessment is our interpretation of the sources below, not an external review.
The new History model strengthens explanation retrospectively; agreement with the
36 cells used to develop it is not prospective prediction.

## Claim ledger

| Proposed claim | Closest precedent / overlap | What our evidence adds | Disposition |
| --- | --- | --- | --- |
| Partial-state, action-constrained TLA+ trace checking | Cirstea et al. [S1] directly formulate constrained trace compatibility; Howard et al. [S2] use trace validation in a deployed system | Application to approval and caller cleanup, including four new retained Cleanup traces | Established method applied to a case; reject methodological novelty |
| Mechanically linking code executions to models | TraceLink [S3] automates mappings in the PGo/MPCal setting and studies environment/compiler deviations | Manual mappings for an existing asynchronous Python implementation | Narrower machinery, different setting; neither extraction nor an advance over automation |
| Cancellation can be suppressed during cleanup | Python's task semantics explicitly permit interception and suppression [S4] | A specific helper consumes caller cancellation, with both child responses reproduced | Case-specific defect, not a new cancellation phenomenon |
| A fresh-correct repair can break old workflow replay | Temporal documents incompatible activity-code changes, markers, and replay testing [S5]; Azure documents preservation of old orchestrator paths [S6] | Controlled cancellation-triggered command omission and measured B/C/V histories | Concrete engineering evidence; reject a general discovery claim |
| Migration safety depends on execution history | Workflow-migration research already defines history-based consistency [S7] | Ordered SDK commands and non-deprecated markers in this particular system | Different semantics and artifact, not a new general migration criterion |
| Permission, invocation outcome, and history compatibility should be checked separately | The above sources already cover much of the constituent reasoning | One connected source-to-model-to-execution example with a bounded remedy | Useful synthesis; originality and transfer value require outside assessment |
| Formal checking detects more bugs than tests | Our own frozen comparison is the relevant evidence | No trace-only detections beyond both test arms | Unsupported; retain the negative finding |

## Primary sources and reading scope

**S1.** Cirstea, Kuppe, Loillier, Merz, *Validating Traces of Distributed Programs
Against TLA+ Specifications*, SEFM 2024. [Author version v2](https://arxiv.org/html/2404.16075v2).
Reviewed instrumenting/atomicity discussion, section 4's trace-compatibility construction,
and limitations. Compatibility is existence of a behavior consistent with both the
specification and observations; it does not establish universal refinement. This
is the closest methodological precedent for our Cleanup bridge.

**S2.** Howard et al., *Smart Casual Verification of CCF*, NSDI 2025.
[Paper](https://www.usenix.org/system/files/nsdi25-howard.pdf).
Reviewed sections 6–8, especially effort, discrepancies, and results. Their work
already connects model/implementation alignment, trace checking, concrete defects,
and ongoing CI. Our case should be compared by what it reveals and costs, not merely
by the presence of TLA+ and tests. Historical effort in our work was not measured.

**S3.** Hackett and Beschastnikh, *TraceLinking Implementations with Their Verified
Designs*, OOPSLA 2025. [Author paper](https://www.cs.ubc.ca/~bestchai/papers/oopsla25-trace-link.pdf).
Reviewed introduction, sections 3–4, and evaluation framing in section 9. TraceLink
uses the structure of PGo-generated implementations to automate trace interpretation.
It also treats assumptions and compiler/runtime behavior as possible sources of
mismatch. It does not establish that arbitrary existing Python can be extracted
correctly; our manual mapping should not be described as comparable automation.

**S4.** Python 3.12 documentation, [Coroutines and Tasks](https://docs.python.org/3.12/library/asyncio-task.html).
Reviewed Task, cancel, cancelled, uncancel, and cancelling. Cancellation is a request,
and task state distinguishes pending requests from completed cancellation. This
supports the need to distinguish the caller from the evaluator; it does not decide
the harness's application-level contract. Maintainers must assess that contract.

**S5.** Temporal, [Python workflow versioning](https://docs.temporal.io/develop/python/workflows/versioning).
Reviewed patch introduction, marker handling, deprecation, and replay testing.
The guide already explains preserving old activity paths and rejecting missing
non-deprecated markers. Our patch uses that established mechanism. The experiment
pins SDK 1.32.0; this source review covers the documentation retrieved on the review
date and does not retroactively change the measured dependency version.

**S6.** Microsoft, [Orchestration versioning](https://learn.microsoft.com/en-us/azure/durable-task/common/durable-orchestration-versioning).
Reviewed version association, version-aware logic, and version matching. Instances
retain their version, and old activity paths must be preserved for replay. This
is evidence that the migration concern extends beyond Temporal in existing practice,
not experimental validation of our model on Azure. Do not transfer Temporal's patch
marker semantics to another engine without a separate mapping.

**S7.** Bakshi and Joshi, *A History Equivalence Algorithm for Dynamic Process
Migration*, arXiv preprint, 2024. [Version 1](https://arxiv.org/html/2412.08314v1).
Reviewed definitions in section 3 and algorithm framing in sections 4–6. Its history
equivalence uses sets of transitions; chronology can be abstracted away for its chosen
migration criterion. That is not the ordered command/marker compatibility required
by our probe. The paper provides a close migration precedent, not a theorem directly
applicable to our History model. Peer-reviewed publication status was not established.

## Search record and exclusions

Searches covered: `formal verification durable workflows replay versioning cancellation`,
`model based trace validation distributed systems TLA implementation traces`,
`asynchronous cancellation semantics structured concurrency formal verification`, and
`workflow evolution instance migration correctness dynamic change workflow`.
A second search engine checked authoritative coverage, followed by direct inspection
of author papers and official runtime documentation. This is a focused comparison,
not a systematic review, exhaustive search, or claim of publication priority.

Newly inspected material includes TraceLink and the history-equivalence preprint;
they materially narrow the possible contribution. CQS (arXiv:2111.12682) was screened
at abstract level only; HTML retrieval failed, so no detailed claim rests on it.
FAVA full text remains unresolved after another HTML retrieval failure. The earlier
agent-policy sources retain their stated reading scopes in the related-work review.
Search hits from forums, aggregators, and general blogs were not used to establish
technical claims here. No assertion that prior work lacks our exact combination is
based on silence in this search.

## Consequence for the next experiment

Do not run another toy cancellation/patching example merely to repeat documented SDK
behavior. A second case is worthwhile only if it tests transfer of an explicit
analysis procedure on a previously unmeasured implementation, with predictions fixed
before execution and failures retained. The [prospective-case gate](prospective-case.md)
defines selection, falsification, and stopping rules. No qualifying second case has
been selected or run yet. Independent review should first decide whether this would
test a scientifically distinct hypothesis against the closest existing methods.
