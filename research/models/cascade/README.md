# Coupled approval gates and policy cascades

This model extends `Approval` rather than duplicating its evaluator, cancellation,
closure, or dispatch transitions. It studies two **already registered gated calls**.
Future calls that bypass the gate under an allow-list are not represented.

## Contract extracted from the implementation

| Operation | Contract | Code evidence |
| --- | --- | --- |
| Approve with remember | Resolve the initiating call, publish it, add its tool name to the live allow-list, then release eligible pending calls | `_handle_tool_approval`, `_apply_policy_update` |
| Deny with remember | Deny the initiating call; do not change policy | `_handle_tool_approval` approved-and-remember branch |
| Replace policy | Install policy and synchronously re-evaluate pending entries | `set_approval_policy`, `_apply_policy_update` |
| Tighten policy | Leave settled approvals/denials unchanged; pending ineligible calls remain pending | Iteration over `pending_approval_entries` only |
| Cascade publication | Initiating remembered resolution precedes sibling resolutions; siblings follow registration order | `_resolve_and_publish` before policy update, pending-entry iteration |
| Evaluator after cascade | A settled entry supersedes the evaluator; cleanup must finish before gate finalization | `_run_auto_mode_evaluator`, `_cancel_and_settle` |

This is tool-name authorization. A remembered approval can release another call of
that tool with different arguments. The study does not reinterpret it as an
argument-specific grant. All experiment tools are harmless.

## Model construction

- `allowed` is the live set of eligible tool names; inherently-safe flags are false,
  skip-all is off, and the auto-mode switch stays enabled.
- `ToolOf` maps calls to either the same name or two different names.
- `CallOrder` is the evidenced registration sequence: both a-then-b and b-then-a
  are exercised. Tool identity remains fixed to the call when order changes.
- `Remember` combines the accepted human decision and synchronous cascade into one
  action. `Update` combines policy replacement and synchronous cascade.
- `BaseStep` wraps the original `Next`, accumulating resolution history without
  changing its state-machine semantics.
- `history` abstracts actual resolution publications; `causes` records the causal
  pairs established by a remembered decision. `scopeViolation` is a history monitor
  for release outside eligibility, not an implementation field.
- Policy replacement can relax or restrict eligibility at any point, including
  cancellation unwinding. Accepted approvals are not revoked by restriction.

## Checks

Normal SameTool and DifferentTools configurations check type consistency, decision
stability, single resolution, authorized dispatch, denial enforcement, cascade
scope, and cause-before-cascade ordering. Liveness checks eventual caller outcome
under weak fairness for consuming evaluations, completing cancellation, and
finalizing gates. It does not require humans to answer or evaluators to terminate
before another decision/closure occurs.

Three isolated synthetic faults must yield their named invariant violation:

| Fault | Required detector |
| --- | --- |
| Release calls regardless of tool eligibility | ScopePreserved |
| Re-resolve an already settled call | SingleResolution |
| Publish cascade before its initiating remembered decision | CauseBeforeCascade |

Mutation configurations bound corrupted entries to at most two resolutions so the
fault experiments remain finite. Normal configurations never re-resolve an entry.
These model faults are not confirmed defects in production code.

## Real Temporal validation

`test_policy_cascade.py` records twelve scenarios under both registration orders:

1. Remember before the sibling evaluator denies.
2. Evaluator denial before remember.
3. Human denial before remember.
4. Denial carrying remember (no policy change).
5. Policy relaxation while both evaluators are blocked.
6. Restriction after cascade approval while evaluator cleanup is delayed.
7. Remember for one tool while a different tool remains pending.
8. Close flag set immediately before accepted remember in one handler.
9. Accepted remember immediately before close in one handler.
10. Evaluator approval before remembered approval.
11. Evaluator escalation before remembered approval.
12. Evaluator failure before remembered approval.

Scenarios 8 and 9 exercise concrete synchronous orderings of internal operations. They
are not a claim that separate network requests can reliably be scheduled between
closure and finalization, or that the session admits arbitrary work after close.

Snapshots read actual statuses, allowed names, close flag, recorded resolution
history, and completed caller outcomes. They are recorded after operator actions,
not halfway through the synchronous cascade. Raw events retain intermediate
publications and the tests independently assert resolution uniqueness and causal
order. Observers introduce no new awaits in the production policy paths.

The schema-2 checker extends Cascade with an observation cursor. Accepted human,
remembered, policy, close, and evaluator-completion inputs are recorded explicitly.
Each such cursor step executes that exact model action and checks its successor
projection. Only Consume, Cancelled, and Finalize may be hidden. The checker cannot
invent another human response, policy replacement, closure, or evaluator verdict.
This is bounded action-constrained conformance of partial states, not a refinement
proof. Five invalid controls test denied dispatch, overwritten denial, unrecorded
policy, wrong initiating cause, and wrong decision input. Missing, stale, incomplete,
or unsupported scenario evidence fails CI. Clean old trace output before regeneration.

The single-call checker now uses the same recorded-input restriction. Earlier
schema-1 evidence used broader hidden steps and is distinguished in the history.

## Reproduce and artifacts

```bash
python research/scripts/check_cascade.py --jar /path/to/tla2tools.jar
uv run --frozen pytest tests/research/test_policy_cascade.py -q
uv run --frozen python research/scripts/check_cascade_traces.py --jar /path/to/tla2tools.jar
```

The runners copy the current Approval module into generated result directories;
there is no independently maintained second copy. CI uploads model logs and
hashes, raw events/projections, generated trace modules, witness/rejection logs,
and JUnit results. Read the exact CI commit for empirical results.

## Limits

Two calls, both registration orders, abstract tool-name eligibility, valid immutable
inputs and verdicts, trusted operator updates. No operator authentication, policy
criteria edits, auto-mode toggling, arbitrary policy layers, arbitrary call count,
external effects, replay equivalence proof, or implementation refinement theorem.


## Implementation sensitivity and robustness finding

`check_implementation_mutations.py` runs isolated copies of the Python implementation.
Its baseline must pass; four selected faults must produce regression failures without
setup errors. Import provenance is asserted before pytest starts. These experiments
measure selected fault sensitivity, not general detector accuracy.

The separate malformed-superseded-result Temporal regression does not export a Cascade
trace: it deliberately violates the earlier valid-result input assumption. See the
[minimal finding and patch](../../upstream/superseded-result.md),
[critical assessment](../../review-assessment.md), and [related work](../../related-work.md).
