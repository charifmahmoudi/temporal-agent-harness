# Approval implementation correspondence

## Question and evidence standard

Can a legal execution of the bounded Approval TLA+ specification explain each
ordered sequence of observations recorded from controlled Temporal executions?
This is existential conformance of partial observations. It is not a refinement
proof, exhaustive scheduler exploration, or verification of all Python behavior.

## Atomicity audit

| Concrete boundary | Model treatment | Evidence / limitation |
| --- | --- | --- |
| Accepted human update | Human | Validator and handler have no suspending await for remember=False; update validation/scheduling is a Temporal assumption, not proven here |
| Evaluator task returns | Complete | Probe records immediately before return with no intervening await; task completion is separate from runner consuming result |
| Wait for done or settlement | Consume enabled condition | Real workflow.wait_condition used; completion alone does not override existing settlement |
| Ordinary evaluator result | Consume | Awaiting an already completed task does not suspend; event publication and application contain no await on valid return path |
| Superseded evaluator | Consume -> cancelling -> Cancelled | `_cancel_and_settle` awaits actual task unwinding; explicit cleanup barrier tests that the caller stays blocked |
| Close signal | Close | Synchronous flag change; previously accepted approvals survive |
| Gate finalization / dispatch | Finalize | Finalizer is synchronous; inline tool_start follows approval return without a suspending await |

The observer subclass delegates to original methods. Observation append and snapshot
operations are synchronous. No production method is edited and no Temporal wait or
scheduler is monkeypatched. Instrumentation can affect performance; equivalence of
all instrumented and uninstrumented executions is not proven.

## Controlled scenarios

Seven independent executions use an inline harmless tool and a real Temporal
 time-skipping test server:

- Human approval while the evaluator is blocked.
- Human denial while the evaluator is blocked.
- Evaluator approval with no human response.
- Evaluator denial with no human response.
- Closure with a pending evaluator.
- Human approval followed by cancellation with delayed cleanup. A query confirms no
  tool_start and no caller completion until cleanup is released.
- Evaluator release and human approval enabled in a single update handler. This tests
  one concrete controlled order; it does not force evaluator completion before human
  resolution, and is not evidence for all possible simultaneous-ready schedules.

The query for evaluation_started is a barrier: the evaluator is waiting on a release
condition initially false. Client polling is used only to detect barrier/outcome
arrival, not to establish race order by elapsed time. Thirty-second deadlines fail
stalled experiments. Workflow IDs, raw lifecycle events, projections, and implementation
hashes are saved. The evaluator's own return/cancellation markers supplement events.

## Projection and checker

Every projection reads actual approval-entry status and the runner close flag.
Additional fields come from observation sites:

| Site | Additional abstract observation |
| --- | --- |
| Evaluation started | evaluator=running, phase=evaluating |
| Evaluator returns | evaluator=done, verdict=approve/deny |
| Cancellation received | evaluator=cancelling, phase=cancelling |
| Tool start / successful caller finish | phase=dispatched |
| ToolApprovalDenied caught by caller | phase=rejected |
| Resolution, close, runner return | No inferred phase/evaluator state |

The schema-2 checker generates a module extending the actual Approval specification.
Recorded human, closure, and completion inputs execute their matching action at the
cursor step; that successor must match the observation. Hidden Consume, Cancelled,
and Finalize transitions are allowed between observations. No hidden human response,
closure, or evaluator completion is allowed. TLC searches for cursor completion; an expected TraceNotMatched counterexample supplies
a witness model execution. The generated module and witness log are artifacts.

This allows unobserved internal model actions. It establishes existence of a consistent model
execution, not exact action-by-action correspondence or completeness of recording.
Unexpectedly permissive abstractions can accept traces; additional fields and
negative controls reduce, but do not eliminate, that risk.

Three fabricated traces must be rejected after completed exploration: dispatch while
 denied, approved reverting to pending, and approval with no recorded input. Missing scenarios, stale implementation
hashes, missing terminal observations, unsupported fields, parse/tool failures, and
timeouts fail CI. Synthetic traces are not implementation findings.

## Cancellation and progress

The original model collapsed cancellation into immediate completion. This revision
exposes cancelling explicitly. Weak fairness of Cancelled encodes eventual cleanup;
without it the model permits indefinite blockage after an accepted human decision.
The delayed-cleanup experiment demonstrates this dependency for a finite delay,
not termination for arbitrary evaluators. A cancellation-resistant evaluator remains
outside the claimed progress guarantee.

## Reproduce

```bash
uv run --frozen pytest tests/research/test_approval_traces.py -q
uv run --frozen python research/scripts/check_traces.py --jar /path/to/tla2tools.jar
```

CI uploads traces, generated checker modules/configurations, witness/rejection logs,
summary, and test results. Read CI evidence for the exact commit being evaluated;
local collection or boundary-test success is not real-server evidence.


## Subsequent fidelity audit

Both schema-2 checkers now prohibit hidden human, close, and evaluator-completion
inputs; the coupled checker also prohibits hidden remembered and policy inputs. See
[Cascade](models/cascade/README.md). Earlier schema-1 runs used broader hidden Next
transitions and must not be described as satisfying the stronger criterion.

Challenging the valid-result assumption exposed a malformed superseded-result defect
in `_run_auto_mode_evaluator`. A type guard preserves settled outcomes and terminal
publication; valid-verdict model transitions are unchanged. The source-map manifest
records that review. The [finding](upstream/superseded-result.md) includes standalone
regressions, a real Temporal branch experiment, and isolated reintroduction evidence.
This finding originated in inspection and targeted execution, not a TLC counterexample.
