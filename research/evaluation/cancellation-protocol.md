# Cancellation and recovery investigation — protocol v2

[Case study](../../RESEARCH.md) · [v1 comparison](results-v1.md)

## Question and provenance

Does accepted settlement remain safe and live when evaluator cleanup is delayed,
raises, returns after cancellation, or receives a second cancellation from its caller?
Do controlled histories preserve these outcomes after worker restart and replay?
The unmodified study baseline is `7bad5ca9957fad872c4dfb4df28b8c1e8a3d843c`.
This protocol precedes the Temporal experiments; v1's corpus and scores stay unchanged.

Inspection found a candidate in `_cancel_and_settle`: it catches child and caller
`CancelledError` together. A preliminary asyncio experiment showed a cancelled parent
returning normally with a nonzero cancellation count. This is known pilot evidence,
not a model-generated discovery or a demonstrated Temporal workflow-cancellation bug.

## Hypotheses

| ID | Hypothesis | Required experiment |
| --- | --- | --- |
| H1 | Ordinary cleanup exceptions or returned verdicts cannot replace accepted settlement. | Approval, denial, and close crossed with cleanup propagation, exception, and return |
| H2 | Settlement alone does not imply caller or close completion without cleanup termination. | Barrier-controlled delayed cleanup; explicit blocked-prefix observation then release |
| H3 | Cancelling the caller during cleanup may be swallowed and permit tool dispatch. | Supported custom agent signal cancels its handler task after cleanup begins; second child cancellation raises or returns |
| H4 | Worker restart/replay preserves the controlled cleanup outcome. | Restart while cleanup waits, compare state, release, retain history, replay |
| H5 | Workflow cancellation is distinct from caller-task cancellation. | Public WorkflowHandle.cancel control; inspect workflow terminal status |

H3's proposed contract forbids dispatch when cancellation reaches the waiting caller
before dispatch. It does not revoke an earlier approval, undo an external effect, or
claim that every workflow cancellation cancels every spawned task. H2's finite prefix
cannot prove infinite runtime nontermination; the formal blocked-cleanup model supplies
an infinite counterexample under an explicit nontermination assumption.

## Method and scoring

Use public message, approval, close, signal, query, and workflow-cancel APIs. The custom
evaluator supplies supported asynchronous cleanup behavior. A synchronous observer
retains events; no await is inserted into production approval paths. The signal in
H3 uses standard asyncio cancellation of the recorded handler task, not a private
harness handler. Readiness and cleanup barriers establish ordering; elapsed time is
not evidence of a winner or liveness violation.

Run the unmodified baseline first. Retain evidence before assertions. Each completed
history is replayed with the same workflow definition and converter. Restart is a
graceful worker replacement using a fresh worker/cache; it is not a process-kill,
server-failure, or mixed-version upgrade experiment. The replay checker establishes
command compatibility for these histories, not a universal replay proof.

If H3 reproduces, validate an isolated minimal correction with the same stimuli and
ordinary cleanup controls. Protect both cases: the child raises on second cancellation,
and the child suppresses it and returns. Do not modify the baseline merely to make
the proposed contract pass. A prepared patch is not upstream acceptance.

Setup errors, missing history, replay failures, and timeouts are experiment failures.
Expected contract counterexamples must have accepted approval, evidenced caller
cancellation, and a later concrete tool-start event. Actual source hashes, event
histories, JUnit results, pinned model-tool hash, and TLC logs are retained in CI.

## Scientific interpretation

Distinguish decision stability, caller cancellation, close draining, and workflow
cancellation. A reproduced H3 is a robustness defect against the helper's stated
propagation intent; deployment incidence and severity remain unmeasured. H2 may be a
contract limitation rather than an implementation bug. Supported SDK cancellation
semantics permit cleanup and suppression; the relevant primary reference is the
[Temporal Python SDK cancellation documentation](https://github.com/temporalio/sdk-python/blob/main/README.md#asyncio-cancellation).
Independent review is still required for abstraction, atomicity, and generality.

## Operational amendment after first CI attempt

Run 37891291257 reproduced the caller-cancellation behavior and passed the other
Temporal controls, but its idle post-replacement query timed out. The restart
procedure now sends a no-state-change checkpoint signal before querying, so a new
workflow task is scheduled rather than depending on idle sticky-query routing.
The desired recovered state and scoring are unchanged. The first model attempt
also had a runner diagnostic mismatch: TLC emitted the named singular
`Temporal property CleanupProgress was violated.` rather than the plural string.
The runner now requires that exact named diagnostic and exit 13. The first attempt
remains retained as an incomplete run; it is not presented as a successful study.

A second attempt (37891534941) passed the six model checks but again timed out while
waiting specifically for the original `cleanup_entered` observer flag after restart.
The next attempt retains the first recovered query and accepts either a waiting
cleanup state or an already completed invocation for measurement. Exact state equality
is recorded as `matches_before`, not assumed. Stable approval and final outcome are
still asserted, and the complete history is replayed. This changes H4's measurement
procedure, not its interpretation: a false equality result must be reported as a
reconstruction discrepancy, not as preservation of the waiting cleanup state.

The third attempt (37891860332) still failed its first recovered query with an RPC
deadline, before any recovered state was available. This is **not evidence of a
state-reconstruction discrepancy**. The replacement experiment now explicitly
disables workflow caching (`max_cached_workflows=0`) on both workers, avoiding sticky
query routing in the test server. Its claim is limited to replacement with nonsticky
execution. Production sticky routing, process crashes, and server failures remain
untested. The preceding incomplete attempts remain linked in the final report.

Run 37892043434 passed 23 baseline and 23 helper-only corrected tests, the six model
checks, and 16 history replays per variant. Review of its raw events showed that
the corrected caller path lacked an evaluation terminal. The proposed correction
now also closes the superseded bracket on live caller cancellation before raising;
offline workflow eviction is guarded from publication. Both caller tests now require
exactly one superseded terminal. The helper-only correction is intermediate evidence,
not the final proposed patch. This amendment strengthens audit-completeness validation.

## Model-fidelity amendment

After run 37893301777, review of the raw BlockedProgress counterexample found that
the inherited Consume action could place an already-completed evaluator in a
cancellation phase that CleanupCanFinish=FALSE disabled indefinitely. Awaiting a
done task cannot create that concrete wait. Cleanup now records whether Consume
actually superseded a running evaluator; completed tasks retain an enabled finish
action. Every configuration checks ReadyTaskNotBlocked and PendingCleanupPhase.
The previous model evidence is retained as intermediate evidence; only the refined
model is used for the final cleanup-progress interpretation. The concrete caller
reproductions and proposed Python correction are unchanged.
