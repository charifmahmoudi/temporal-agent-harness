# Critical assessment and weakness ledger

This is the author's adversarial self-assessment using research-review and upstream
contributor criteria. It is not independent peer review, maintainer acceptance, or a
conference recommendation. Evidence and unresolved obligations are tracked together.

| Weakness | Concrete work | Research-review judgment | Upstream-contributor judgment | Remaining obligation |
| --- | --- | --- | --- | --- |
| Permissive correspondence | Both schema-2 checkers record operator inputs and evaluator results. Only Consume, Cancelled, and Finalize can be hidden. Negative controls reject invented policy, wrong input, and wrong cause. | Material improvement: witnesses cannot manufacture missing external decisions. Still bounded partial-observation conformance, not a refinement theorem. | Useful guard against model/observer drift; raw events remain auditable. | Prove or independently review observation completeness and atomicity. Earlier schema-1 evidence is retained as historical evidence only. |
| Narrow schedule coverage | Twelve coupled scenarios run under both registration orders. Added evaluator approval, escalation, and error before remembered approval. Safety configurations exercise both orders. | Named coverage is stronger than increasing a test count without new behaviors. No exhaustive Temporal scheduler coverage or arbitrary-call proof. | Regressions cover order-sensitive publications and fail-safe paths using barriers rather than timing races. | Three-call cascades, mode/criteria changes, replay, and arbitrary policy layers remain open. |
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

The engineering artifact can be strengthened and the concrete fix made reviewable in
this iteration. A universal Python-to-TLA+ refinement proof, independent review, and
cross-framework evaluation cannot be manufactured from these experiments. Those
obligations remain open, with explicit evidence needed to close each one.

For a research committee, the appropriate posture is an evidence-backed case study
under development. For an upstream maintainer, it is a narrowly scoped robustness fix
with useful regressions. The latter can be valuable even if the eventual paper does
not meet a major conference's novelty threshold.
