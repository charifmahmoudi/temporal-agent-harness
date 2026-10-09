# Policy-cascade interpretation and evidence requirements

This report states testable interpretations of the pinned implementation. It does
not claim that finite model checks prove the whole harness correct. A separate
[malformed-result finding](upstream/superseded-result.md) concerns gate robustness.

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


## Strengthening iteration: exact-commit evidence

[CI run 37885395663](https://github.com/charifmahmoudi/temporal-agent-harness/actions/runs/37885395663)
passed model and implementation jobs for `128af56bc2b904aa4929b604824fb8d397ff6c62`:

- 82 selected implementation tests passed, including 24 coupled traces under both
  registration orders, twelve standalone malformed-result cases, and a separate
  real Temporal malformed-superseded-result regression.
- Thirteen model configurations produced the expected result, including both
  registration orders for same-tool and different-tool safety checks.
- All 24 coupled traces matched their recorded inputs under schema 2; all five
  coupled invalid controls were rejected. The seven initial traces and their two
  controls also passed under the earlier partial-observation criterion.
- The isolated seven-test baseline passed. All four actual Python mutations were
  detected: denial remembering, scope leakage, and reversed publication each
  produced two assertion failures; removing superseded-result validation produced
  one real Temporal regression failure. No collection/setup errors were counted.

The standalone patch also applied cleanly to the pinned original baseline, where its
twelve regression cases passed after application. The new defect is a robustness
failure under malformed plugin output and competing settlement, not evidence that
normal policy restriction revokes approval or that the gate permits denied actions.
The [assessment](review-assessment.md) distinguishes improvements from still-open
refinement, external-validity, and publication obligations.


Both checkers subsequently received the same recorded-input restriction. The current
single-call negative suite adds approval without a recorded decision. Its exact-commit
validation is reported separately from the schema-1 historical evidence above.


[CI run 37885725766](https://github.com/charifmahmoudi/temporal-agent-harness/actions/runs/37885725766)
passed both jobs for `d3c3f9b3c6c45cd2a6d8afbda4f6dcc2f75c0f1d`. All 31 recorded
traces now use schema-2 recorded-input constraints, and all eight invalid controls
were rejected. The 82 selected tests, thirteen model configurations, and four
implementation-mutation experiments also passed. Separately, the complete repository
suite passed on Python 3.11, 3.12, 3.13, and 3.14 for the preceding fixed revision
([matrix run](https://github.com/charifmahmoudi/temporal-agent-harness/actions/runs/37885395560));
the Python 3.12 job reported 889 passing tests.
