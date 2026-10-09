# Policy-cascade interpretation and evidence requirements

This report states testable interpretations of the pinned implementation. It does
not claim a new defect or that finite model checks prove the whole harness correct.

## Questions

- Can remember overwrite an earlier sibling denial?
- Can a later evaluator deny a call already released by a policy cascade?
- Does a restrictive policy revoke accepted approval during delayed cleanup?
- Are unrelated tool names isolated and resolution events causally ordered?
- What happens when closure and remembered approval execute in either order before
  pending-gate finalization?

## Reproduced results and evidence

| Interpretation | Model evidence | Implementation scenario |
| --- | --- | --- |
| Settled denial is preserved | DecisionStable / SingleResolution | evaluator_deny_first, human_deny_first |
| Cascade approval supersedes in-flight evaluation | Inherited Consume / cancellation transitions | remember_first, policy_relax |
| Restriction is not retroactive revocation | Update changes only pending entries | tighten_after_release |
| Remember on denial has no allow-list effect | Ordinary denied Human transition | denied_remember |
| Other tool remains gated | ScopePreserved / DifferentTools | different_tool |
| Cause publishes before sibling despite opposite registration order | CauseBeforeCascade | remember_first and closure variants |
| Close flag alone does not invalidate an accepted pending decision | Close followed by Remember before Finalize | close_first |

The complete verification workflow passed for commit
`e56587039ff864ac9e206e956e0f89d117af10f8`:
[CI run 37883632980](https://github.com/charifmahmoudi/temporal-agent-harness/actions/runs/37883632980).
Both the model and implementation jobs succeeded. The run established:

- 54 selected implementation tests passed, including nine coupled-policy scenarios.
- All 11 model configurations produced their expected results: four normal safety
  configurations, two conditional-progress configurations, and five synthetic faults.
- All 16 recorded implementation traces admitted ordered partial-observation model
  witnesses; all four deliberately invalid traces were rejected.
- The AST correspondence guard passed for the pinned implementation functions.

The run retains raw events, projections, generated trace specifications, TLC logs,
module hashes, and JUnit results. These are bounded checks and controlled executions.
A witness permits hidden model actions; it does not establish implementation
refinement or comprehensive schedule coverage. No production defect was confirmed.

During validation, an observer initially exposed intermediate publications inside
synchronous policy replacement. The corrected observer records stable operation
boundaries while retaining every raw publication. This aligns the projection with
the documented atomic model action rather than weakening the invariant.

## Practical consequence

The contract is **first accepted resolution**, not last writer wins; policy
restriction affects eligibility rather than revoking accepted decisions. Closure
finalization and cancellation cleanup are separate stages. Users requiring revocable
permissions need a different explicit contract and mechanism. This case study does
not prescribe one or claim the current contract is a security bug.
