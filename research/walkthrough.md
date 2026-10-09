# One approved call, three correctness questions

[Case study](../RESEARCH.md) · [Argument and claim boundaries](storyline.md)

A human approves a tool call while its automatic evaluator is still running. The
harness accepts the human decision and cancels the now-unneeded evaluator. While
waiting for that evaluator to finish cleaning up, the caller itself is cancelled.
Should the tool still run?

The contract studied here says **no**. Approval records permission; cancellation
stops this invocation. Keeping the approval in the audit record does not require
executing the cancelled invocation. This is the contract we test, pending independent
review and maintainer confirmation of intended behavior.

The baseline can nevertheless continue to dispatch. A direct correction stops it
in fresh executions, but an existing workflow may already have recorded the old
activity command. That history creates a second obligation for the replacement code.
This walkthrough follows that one case from source to model to retained evidence.

## 1. What the code is doing

There are two tasks: the **caller**, waiting to run the tool, and its **evaluator
child**, deciding whether to approve. Cancelling the child because a human already
answered is different from cancelling the caller because its invocation should stop.
Neither is the session-close flag, and neither should be confused with a request to
cancel the entire Temporal workflow.

All source names below are in [agent_workflow.py](../temporal_agent_harness/harness/agent_workflow.py).
Search for the named function rather than relying on line numbers that move.

| Concrete code | Role in this example | Model boundary |
| --- | --- | --- |
| `_handle_tool_approval` | Accepts the human decision | Approval's `Human`, exposed by Cleanup's `Environment` |
| `_run_auto_mode_evaluator`, `settled()` branch | Observes that someone else settled the gate and waits for evaluator cleanup | `ConsumeStep` |
| `_cancel_and_settle` | Cancels the child, awaits it, and catches `CancelledError` | Cleanup may finish normally; `CancelCaller` represents caller cancellation and the child's completing response |
| `_apply_approval_policy` and the `activity_tool_defn` dispatcher | Passing the gate permits continuation; the dispatcher subsequently calls `workflow.execute_activity` | `FinalizeStep` abstracts gate permission only |

The relevant baseline helper ends with:

```python
 task.cancel()
 try:
     await task
 except (Exception, asyncio.CancelledError):
     pass
```

The catch is intended to discard the superseded child's outcome. In the reproduced
schedule, it can also consume cancellation of the awaiting caller. Moreover, the
child can suppress the second cancellation and return normally, so simply removing
one exception handler is not the whole correction.

The [isolated correction](upstream/caller-cancellation.patch) checks the caller's
outstanding cancellation after the await, including normal return, and propagates it.
It also closes the superseded evaluation's audit record on the tested live path.
The direct and versioned cancellation corrections remain experiment patches;
they are not applied to this branch's production implementation.

## 2. What a model means here

A model is a deliberately smaller executable description of the possible states and
steps. It keeps the accepted decision, whether evaluator cleanup is pending, and
where the caller is. It leaves out LLM reasoning, message payloads, and Temporal's
durable history. A step represents a chosen code boundary, not necessarily one
Python statement.

[Cleanup.tla](models/cancellation/Cleanup.tla) extends
[Approval.tla](models/approval/Approval.tla). It is manually derived from source.
For this case it represents one call, `c1`. The following table is a projection of
the **actual retained TLC counterexample**, `CurrentCancellation.log` inside
[model.zip](evaluation/cancellation-evidence/model.zip). No steps have been added.

| State / incoming action | Accepted status | Caller phase | Cleanup pending | Caller cancelled | Outcome |
| --- | --- | --- | --- | --- | --- |
| 1 / initialization | pending | evaluating | false | false | none |
| 2 / `Environment` (human approves) | approved | evaluating | false | false | none |
| 3 / `ConsumeStep` | approved | cancelling | true | false | none |
| 4 / `CancelCaller` | approved | gate | false | true | none |
| 5 / `FinalizeStep` | approved | dispatched | false | true | dispatched |

At state 2, `first` becomes approved and `resolutions` becomes 1. Both remain
unchanged through state 5. The evaluator goes from running to cancelling to stopped.
`CancelCaller` abstracts cancellation reaching the waiting caller **and** the child's
response ending that await. It does not assert that every child must terminate.

## 3. Which property fails, and why it matters

A property is an explicit condition we want every allowed execution to respect.
Different properties protect different interests:

| Property | Question it answers | This counterexample |
| --- | --- | --- |
| `DecisionStable` | Can a later result replace the first accepted decision? | Preserved: approval remains approval |
| `SingleResolution` | Can the call acquire multiple accepted resolutions? | Preserved: the count stays 1 |
| `AuthorizedDispatch` | Does every dispatch have approval? | Preserved: the call is approved |
| `CallerCancellationRespected` | Can this invocation dispatch after caller cancellation during cleanup? | Violated at state 5 |

The failing invariant is `callerCancelled => outcome != "dispatched"` in every
reachable state. A system can therefore preserve permission perfectly while still
performing work that its caller cancelled. This is why checking approval alone is
insufficient for this contract.

In the corrected model, `CancelCaller` leads to phase `aborted` and outcome
`cancelled`; status remains approved. TLC checks all reachable states of that finite
configuration and finds no violation. This is a bounded model result, not a proof
that every execution of the Python implementation is correct.

Progress is a separate question: will an accepted decision eventually produce an
outcome? If a running evaluator never finishes cleanup and no completing caller
cancellation occurs, the caller can remain waiting. Weak fairness means an action
that remains enabled eventually occurs; it cannot make disabled cleanup finish.
The [Cleanup documentation](models/cancellation/README.md) states those assumptions
and the retained blocked-progress counterexample.

## 4. How the model is checked against reality

TLC explores model states. Implementation tests execute Python and controlled
Temporal schedules. Replay tests run replacement code against recorded workflow
history. These are different checks, with different conclusions.

| Evidence | What it supports | What it does not establish |
| --- | --- | --- |
| Six expected Cleanup TLC results | The selected abstract baseline violates cancellation respect; the corrected configuration preserves it; progress depends on cleanup | Universal Python correctness |
| [Cancellation study](evaluation/cancellation-results.md), 23 tests per variant | The concrete baseline can swallow caller cancellation; the isolated correction handles both child responses in the tested schedules | Every possible runtime schedule |
| Original recorded-input trace checks | Selected Approval/Cascade traces admit legal model executions | A mechanical match of this Cleanup witness to the activity study |
| [Activity study](evaluation/activity-results.md), fresh runs | Cancellation can precede a real activity schedule and a test-ledger write in baseline; corrected variants prevent both in the tested new paths | Exactly-once effects or rollback in arbitrary external services |

The source-to-state explanation above is a **manual explanatory alignment**.
Cleanup is not covered by the original schema-2 trace checker. The defect was found
through inspection and targeted execution; TLC did not discover it in the source.
Its contribution here is to make the missing obligation and assumptions explicit.

A green CI run includes expected failures: the baseline model must produce the named
invariant violation, while the corrected model must pass. Baseline characterization
tests can pass by reproducing a defect. “CI passed” never means “baseline is correct.”

## 5. Why the correction also needs an upgrade story

Temporal records activity commands in workflow history. In the retained baseline
cancellation histories, the cancellation signal is event 15 and the activity schedule
is event 19; activity start and completion follow at 24 and 25. The activity writes a
test-only ledger outside workflow memory. This extends the inquiry beyond the model's
abstract permission to dispatch.

Three code variants were measured: **B**, baseline; **C**, direct correction; and
**V**, correction guarded by `workflow.patched("approval-caller-cancel-v1")`.

| Situation | Measured result | Meaning |
| --- | --- | --- |
| Fresh caller cancellation, with either tested child response | B schedules and writes once; C and V schedule nothing and write nothing | The correction protects these new invocations |
| Replay B's cancellation history with C | Explicit nondeterminism: `No command scheduled for event HistoryEvent(id: 19, ActivityTaskScheduled)` | Fresh behavior is corrected, but old command history is incompatible |
| Replay the same B history with V | Compatible in the tested cells | The version branch preserves the historical path |
| Live B → V replacement before cancellation | New cancellation prevents dispatch | Tested new work takes the corrected path |
| Live B → V replacement after activity completion | Old effect remains once; no second write | Compatibility preserves history; it does not undo the effect |

The study retained 12 fresh executions, 36 replay cells, and eight graceful nonsticky
worker replacements. The direct correction caused explicit workflow-task
nondeterminism in the two post-activity replacement cases; administrative termination
then cleaned up those runs. That is not a claim of terminal workflow failure.
V is not universally migration-safe: some histories produced by unmarked C are
incompatible with V, and rollback safety is not established. See the complete
[compatibility matrix and limits](evaluation/activity-results.md).

No TLA+ model here describes Temporal history or version markers. The upgrade result
is empirical and uses standard Temporal patching; it is not a new patching technique
or evidence of a Temporal defect.

## 6. What has been achieved, and what remains

We now have a concrete case connecting a source defect, an explicit missing property,
a finite counterexample, tested corrections, and a durable-history constraint on
rollout. A separate malformed-evaluator-result defect has a type guard applied on
this branch; [its packet](upstream/superseded-result.md) records that distinct finding.

The central remaining work is independent challenge and reproduction, maintainer
assessment of intended cancellation behavior, and review of supported migration
cohorts. Formal-method superiority is not demonstrated: the frozen comparison found
no trace-only detections beyond both test arms. Publication novelty remains an open
assessment, not a completed milestone.

Continue with the [storyline and claim ledger](storyline.md), then
[reproduction instructions](evidence.md) and the [review packet](evaluation/review-packet.md).
