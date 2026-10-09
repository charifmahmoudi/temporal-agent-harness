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

## Candidate results and their intended evidence

| Interpretation | Model evidence | Implementation scenario |
| --- | --- | --- |
| Settled denial is preserved | DecisionStable / SingleResolution | evaluator_deny_first, human_deny_first |
| Cascade approval supersedes in-flight evaluation | Inherited Consume / cancellation transitions | remember_first, policy_relax |
| Restriction is not retroactive revocation | Update changes only pending entries | tighten_after_release |
| Remember on denial has no allow-list effect | Ordinary denied Human transition | denied_remember |
| Other tool remains gated | ScopePreserved / DifferentTools | different_tool |
| Cause publishes before sibling despite opposite registration order | CauseBeforeCascade | remember_first and closure variants |
| Close flag alone does not invalidate an accepted pending decision | Close followed by Remember before Finalize | close_first |

Successful CI for an exact commit is required before reporting these as reproduced
results. TLC completion, expected synthetic failures, all scenario assertions, and
trace witnesses must pass. The repository workflow retains the evidence as artifacts.

## Practical consequence

The contract is **first accepted resolution**, not last writer wins; policy
restriction affects eligibility rather than revoking accepted decisions. Closure
finalization and cancellation cleanup are separate stages. Users requiring revocable
permissions need a different explicit contract and mechanism. This case study does
not prescribe one or claim the current contract is a security bug.
