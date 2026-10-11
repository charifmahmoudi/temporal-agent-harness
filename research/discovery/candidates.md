# Discovery candidates and exclusions

2026-10-10. Exploratory screen: [protocol](protocol.md), [43 issue records](screen.json),
[collection run](https://github.com/charifmahmoudi/temporal-agent-harness/actions/runs/38059388840).
Nine queries, at most five earliest issues each; duplicates removed. This is a
bounded purposive sample, not a failure-rate or completeness estimate.

## Three candidate questions

| Candidate | Decision and consequence | Evidence and closest prior answer | Cheapest challenge and disposition |
| --- | --- | --- | --- |
| C1: Which recovery operations remain effective when durable replay is incompatible? | Operator chooses repair, cooperative cancellation, or forced termination; completion and compensation differ. | Restate #3656 explicitly explains why cancellation needs compatible replay. Temporal documents cancellation as a workflow task and termination as server-side closure. OSDI 2022 Cancellation in Systems already separates cancellation phases. | Compare compatible and incompatible recovery, then restore original code. Probe two independent engines. Advance to exploration, not a novelty claim. |
| C2: Does durable waiting inherently consume a thread per suspended workflow? | Capacity planning and executor sizing. | DBOS #652 initially alleges this, but the reporter retracts the premise; Restate #4364 alleges a different encoder allocation issue. Neither establishes a common mechanism. | Read discussion before benchmarking. Reject this proposed generalization; no experiment justified on the retracted premise. Resource questions could be studied separately with a new protocol. |
| C3: Does cancellation of an observer contaminate the observed durable execution? | A disconnected client should not inadvertently stall background work under an isolation contract. | DBOS #425 confirms a known bug fixed by PR #427. Async task cancellation propagation already has substantial prior work. Temporal #782 is a callback issue, not independent confirmation of the same durable failure. | Check implementation history and an independent matching case. Reject novelty at this stage: current evidence supports a known regression, not a new general result. |

## Corrections from deep reading

- [DBOS #652 retraction](https://github.com/dbos-inc/dbos-transact-py/issues/652#issuecomment-4329298923): author had misread older code and had not run the alleged affected version. Executor bounds already address the clarified burst concern.
- [Temporal #783 discussion](https://github.com/temporalio/sdk-python/issues/783#issuecomment-2776621253): timeout display does not establish a scheduling penalty; reporter confirmed a second worker proceeds.
- [Restate #3656 explanation](https://github.com/restatedev/restate/issues/3656#issuecomment-3227324174): cancellation blocked by nondeterminism is expected; compatible code or kill are existing remedies. Reproducing it is not discovering a bug.
- DBOS #551, #664, #679 concern distinct concurrency/context/retry behavior. Maintainer responses discuss support or fixes. Do not collapse them into a single causal pattern.
- Restate #2765 already discusses coordinated feature activation; a final comment names the implemented version barrier. Restate #4513 reports a routing/read-consistency problem. Neither supplies new migration theory.

## Nearest work and search limits

[Cancellation in Systems (OSDI 2022)](https://www.usenix.org/system/files/osdi22-sethi.pdf)
studies cancellation requests and bugs across multiple systems and distinguishes
deciding, propagating, and fulfilling cancellation. A relabeled cancellation
taxonomy would overlap it. Our narrower possible empirical question concerns the
operator's recovery choices after durable replay fails, not a new cancellation law.

Official contracts inspected: [Restate invocation management](https://docs.restate.dev/services/invocation/managing-invocations),
[Restate errors](https://docs.restate.dev/references/errors),
[Temporal task errors](https://docs.temporal.io/references/workflow-task-errors),
[Temporal Python cancellation](https://docs.temporal.io/develop/python/workflows/cancellation),
and [DBOS workflow management](https://docs.dbos.dev/python/tutorials/workflow-management).
Searches covered cancellation/replay/recovery and durable upgrade terminology;
this is not a systematic literature review. Recent preprints surfaced but were not
used to establish novelty from titles or inaccessible text. No absence-of-prior-work
claim follows. All three candidates remain grounded in lifecycle-biased selection.
