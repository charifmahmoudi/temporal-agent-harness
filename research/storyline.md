# Storyline: permission, invocation, and durable history

[Case study](../RESEARCH.md) · [Concrete walkthrough](walkthrough.md)

## Central claim

**For the studied tool gate, preserving an accepted approval is insufficient to
respect cancellation of its invocation; correcting that invocation behavior also
requires accounting for previously recorded activity commands.**

This is a bounded implementation case study. Its value is a connected explanation
of a real defect, the contract it exposes, and the measured constraint on its remedy.
It is not a claim of a new verification method or universal upgrade safety.

## The argument, in order

1. **Permission:** human and evaluator decisions compete. First-accepted-decision
   rules prevent a late answer from changing an accepted outcome. Approval and
   Cascade formalize that contract, including policy and publication ordering.
2. **Invocation:** settlement does not finish asynchronous evaluator cleanup. The
   waiting caller can be cancelled there. The baseline may retain approval and
   still dispatch, satisfying decision safety while violating cancellation respect.
3. **Correction:** propagate the caller's outstanding cancellation, including when
   the child returns normally. Preserve the accepted approval and close the tested
   audit bracket. Finite model checks and concrete tests support distinct parts of
   this explanation.
4. **History:** replacement code must also reproduce already-recorded commands.
   The direct fix changes those commands for old activity-bearing histories. A
   standard version marker preserves the tested baseline cohort and protects new
   cancellation paths, with explicit incompatibilities for other cohorts.
5. **Conclusion supported by evidence:** state the permission, invocation, and
   migration obligations separately. Test each at its own boundary; do not infer
   concrete execution or replay correctness from an abstract approval invariant.

The opening example should always be the five-state cancelled-but-approved call in
[the walkthrough](walkthrough.md). Introduce notation after explaining the behavior.
Use the activity mismatch as the consequence of fixing this case, not as an unrelated
second project. Keep Cascade as broader contract context rather than requiring a
reader to master it before understanding the cancellation example.

## Claims and their evidence

| Claim | Evidence to cite | Boundary to state alongside it |
| --- | --- | --- |
| Decision safety does not imply cancellation respect | Retained five-state Cleanup witness; baseline concrete cancellation tests | Manually derived, one-call Cleanup model |
| The concrete baseline can dispatch after caller cancellation | Cancellation study; activity fresh-run history and ledger | Inspection-led discovery; selected controlled schedules |
| The direct correction protects the tested new invocations | C tests, fresh activity runs, harness regression gate | Isolated patch; no universal implementation proof |
| Fresh correctness does not guarantee old-history compatibility | B → C activity replay failures and live post-activity replacements | Workflow-task nondeterminism in this probe, not a Temporal defect |
| A versioned remedy supports the tested B → V migration | Replay cells and both live replacement points | Does not undo an old effect; C → V and rollback are not generally supported |
| Formalization clarifies obligations and assumptions | Explicit cancellation invariant and cleanup-dependent progress witness | Clarification, not measured superiority over testing |

## Honest discovery chronology

The teaching order above is not a claim about how findings were discovered.
Approval/Cascade modeling and trace work came first. The frozen fault comparison
found no trace-only detections beyond both test arms. Inspection and targeted
execution exposed malformed-result handling and caller cancellation. Cleanup then
made the cancellation and progress obligations explicit. Workflow-local replay
showed changed application observations without command mismatch. The subsequent
activity probe exposed command incompatibility and tested the versioned remedy.

These results should remain distinguishable. A workflow-local tool-start observation
is not an external activity effect. The Cleanup witness is not a mechanically matched
schema-2 implementation trace. More experiments do not retroactively establish that
TLC discovered the defect or that the trace method outperformed the test suites.

## Proposed paper structure

| Section | Reader should leave understanding |
| --- | --- |
| Problem and running example | Why an approved invocation might still need to stop |
| System and contract | Human/evaluator competition, cleanup, and the distinct cancellation scopes |
| Abstraction and properties | Which state the model keeps, where steps map to source, and what each property protects |
| Concrete discrepancy and correction | The retained witness, actual Python schedule, and tested repair |
| Durable-history consequence | Why activity history rejects the direct fix and which versioned paths work |
| Evaluation and threats | Frozen negative comparison, bounded checks, cohort limits, and lack of refinement proof |
| Discussion | Practical contract lessons and remaining independent review |

The full property catalogue, Cascade details, historical experiment inventory, and
reproduction commands can support the argument without interrupting its opening.
Do not headline aggregate test counts as the contribution.

## Readiness judgment and next work

The artifact supports a reviewable case study; independent validation and novelty
remain unresolved. The next review should challenge three concrete links:

- **Contract → code:** is preserving approval while aborting this invocation the
  intended behavior, and are other cancellation paths missing?
- **Code → model:** are the action boundaries and child-termination assumptions
  defensible, and do they omit a relevant interleaving?
- **Correction → deployment:** which history cohorts and worker-routing conditions
  can use V, and what additional migration evidence is needed?

The [review packet](evaluation/review-packet.md) requests this evidence. No external
review, maintainer acceptance, production deployment, or conference novelty is claimed.


## Model-connection follow-up

The [retained follow-up results](evaluation/model-bridges.md) add four executable Cleanup trace
checks, rejection controls, and a separate [History boundary model](models/history/README.md).
The History properties distinguish fresh cancellation respect from preserving
baseline or unmarked-correction histories. The model agrees with 36 retained replay
cells, retrospectively. Independent review should challenge the projection rules,
marker abstraction, and omitted schedules; these checks do not establish refinement,
prospective predictive value, or novelty.


## Literature and next-case decision

The [claim-by-claim review](evaluation/novelty-review.md) finds substantial direct
precedent for tracing, cancellation suppression, and replay-aware migration. Our
candidate contribution is the connected, evidenced implementation case, not a new
verification or versioning method. The [review handoff](evaluation/review-quickstart.md)
is ready. A second case should test prospective transfer on independently authored
code under the [selection protocol](evaluation/prospective-case.md); none is selected
or run yet. External review is still outstanding.
