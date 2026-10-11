# Critical assessment and weakness ledger

Current comparative evidence is in the [six-fault assessment](evaluation/assessment.md).
It shows no trace-only detections, two incomplete collectors, and a conservative
scoring limitation. The ledger below also retains the earlier targeted experiments;
those sensitivity results are not comparative superiority results.

This is the author's adversarial self-assessment using research-review and upstream
contributor criteria. It is not independent peer review, maintainer acceptance, or a
conference recommendation. Evidence and unresolved obligations are tracked together.

| Weakness | Concrete work | Research-review judgment | Upstream-contributor judgment | Remaining obligation |
| --- | --- | --- | --- | --- |
| Permissive correspondence | Both schema-2 checkers record operator inputs and evaluator results. Only Consume, Cancelled, and Finalize can be hidden. Negative controls reject invented policy, wrong input, and wrong cause. | Material improvement: witnesses cannot manufacture missing external decisions. Still bounded partial-observation conformance, not a refinement theorem. | Useful guard against model/observer drift; raw events remain auditable. | Prove or independently review observation completeness and atomicity. Earlier schema-1 evidence is retained as historical evidence only. |
| Narrow schedule coverage | Coupled scenarios exercise both registration orders; later studies add retained replay and controlled activity-backed worker replacement. | Named coverage is stronger than a test count. No exhaustive Temporal scheduler coverage or arbitrary-call proof. | Regressions and upgrade cases use explicit barriers and server history. | Three-call cascades, mode/criteria changes, general replay/routing coverage, and arbitrary policy layers remain open. |
| No consequential finding | Challenge the malformed-input assumption; reproduce an unchecked superseded-result read; supply a minimal guard, standalone regressions, real Temporal experiment, and isolated reintroduction. | A concrete discrepancy supports usefulness. It was found by inspection/targeted execution, not model-checker discovery. Its prevalence and severity are unmeasured. | Small patch protects accepted outcomes and closes the evaluation bracket for buggy custom evaluators. | Actual upstream review and acceptance; no deployment incident claimed. |
| Weak detector evaluation | Isolated Python mutations test denial remembering, scope leakage, publication reversal, and malformed superseded results. Baseline must pass; imports are provenance-checked; setup errors do not count as detection. | Shows sensitivity to four selected edits, not general mutation adequacy, false-positive rates, or superiority over ordinary tests. | Demonstrates that regression tests fail for their intended faults. Isolated copies preserve the working package. | Larger independently designed fault corpus and detector ablations if making evaluation claims. |
| Unclear novelty | Primary-source comparison covers trace validation, runtime enforcement, SMT authorization, approval reuse, and agent temporal monitoring. Reading scope is explicit. | Broad novelty claims are ruled out. Candidate contribution is a precise implementation case study and lessons about assumptions and cancellation. | Avoids imposing research claims on a practical bug fix. | Complete screened-paper reading and assess submission genre only after the evidence is mature. |
| Unestablished generality | Separate reusable reasoning obligations from harness-specific API semantics; do not label a second scenario as a second system. | External validity remains open. Two registration orders do not establish cross-framework generality. | The focused patch can stand on its own without the scientific infrastructure. | Another independently analyzed implementation or a parameterized argument is required for stronger generality claims. |

## Acceptance gates

1. Source review: identify concrete non-suspending boundaries and every hidden action.
   Refreshing an AST hash requires an explicit mapping-impact note.
2. Execution: original regressions and expanded Temporal scenarios pass on the fixed
   implementation; fixed-result traces match recorded inputs in order.
3. Sensitivity: the unmodified baseline passes in an isolated copy; each intended
   implementation mutation produces test failures without collection/setup errors.
4. Audit: retain exact commit, module hashes, raw events, projections, witness/rejection
   logs, and JUnit evidence. Report actual defect provenance and bounded scope.
5. Communication: prepare a minimal upstream packet. Do not equate preparing it with
   sending, acceptance, or evidence of customer impact.

## Decision after this iteration

The strongest current evidence is the [activity-backed study](evaluation/activity-results.md).
Both baseline caller scenarios schedule an activity and write the test ledger after
cancellation. C prevents fresh dispatch but produces explicit command nondeterminism
when reconstructing those old histories. V handles the declared B → V cases, including
live nonsticky replacement, while preserving the old effect. All 375 harness
regressions pass under V. The full matrix also records incompatible C → V histories.

**Current committee judgment:** a consequential, reproducible deployment constraint
connects the implementation defect with durable execution. The remedy uses established
Temporal patching; this is not evidence of a novel versioning method or superiority of
formal verification. The case is stronger, but independent scrutiny and external
validity remain unfulfilled.

**Current contributor judgment:** review both the cancellation fix and its history
cohort before rollout. A fix that passes fresh tests can still prevent progress on
old histories. V demonstrates a bounded alternative, not permission for arbitrary
mixed-version operation or retroactive cancellation. Neither packet has been submitted.

The following paragraphs retain the narrower preceding milestones and their limits.

The [offline upgrade experiment](evaluation/upgrade-results.md) now addresses one
previously open evidence question. All 64 history/version cells pass SDK replay,
while four cells change the application projection. Same-version controls and paired
observer-free replays pass. GitHub Actions reproduced all categorical outcomes;
local and CI evidence remain separately identified. This is reproducibility across
two execution environments, not an independent external reproduction.

**Committee judgment:** a concrete witness that command compatibility is weaker than
the measured application agreement, with controls and frozen histories. The probe is
workflow-local, so this must not be inflated into an external-effect or Temporal defect.
Novelty relative to semantic regression testing remains unestablished. The activity-backed
extension above addresses one experimental gap; independent review remains open.

**Contributor judgment:** the patch's intended change in cancellation behavior deserves
explicit rollout review even when replay is green. The isolated correction is still
useful, but these completed-history replays do not validate an in-flight deployment or
determine whether versioning is required for activity-backed integrations.

The subsequent [cancellation study](evaluation/cancellation-results.md) strengthens
the case study with a second reproduced defect and a missing lifecycle obligation:
stable approval is insufficient to guarantee cancellation-respecting invocation.
Both child responses reproduce baseline dispatch; an isolated correction prevents it
and closes exactly one evaluation terminal. Six finite model checks and 32 history
replays support the declared experiment. This remains inspection-led discovery and
selected correspondence evidence. A nonsticky graceful replacement is not general
crash recovery, and a passing corrected model is not Python refinement. The
[minimal upstream packet](upstream/caller-cancellation.md) is prepared, not accepted.

The first frozen comparison is complete. It improves measurement transparency and
identifies collector weaknesses, but does not close the added-value or novelty gate.
The next comparison needs a versioned protocol amendment, early observation retention,
and independently selected faults. See the [current decision gates](maintenance.md).

The engineering artifact can be strengthened and the concrete fix made reviewable in
this iteration. A universal Python-to-TLA+ refinement proof, independent review, and
cross-framework evaluation cannot be manufactured from these experiments. Those
obligations remain open, with explicit evidence needed to close each one.

For a research committee, the appropriate posture is an evidence-backed case study
under development. For an upstream maintainer, it is a narrowly scoped robustness fix
with useful regressions. The latter can be valuable even if the eventual paper does
not meet a major conference's novelty threshold.


The evidence gates above passed in [verification run 37885725766](https://github.com/charifmahmoudi/temporal-agent-harness/actions/runs/37885725766):
82 selected tests, thirteen expected model results, 31 action-constrained witnesses,
eight invalid-trace rejections, and four detected implementation faults. This closes
the reproducibility gates for that commit, not the independent-review or generality
obligations. The focused patch was checked on a clean baseline and its twelve tests
passed after application. See [exact-commit results](findings-policy.md).
