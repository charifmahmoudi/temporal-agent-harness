# Research-question audit protocol

Date: 2026-10-10. Evidence cutoff: published commit
`72ed3d82bf11871d526043cbee6c0d0ad9b675bc`.

## Purpose and status

Audit whether the existing research supports a justified next scientific experiment.
The prior outcomes and source fixes are already known. This is a **retrospective
audit**, not preregistration of those outcomes or a blind validation study. Publish
this decision procedure before executing the new audit in GitHub Actions. All new
runtime experiments, if justified, and executable evidence checks run in GitHub CI.

## Questions to adjudicate

1. Does the adapted Nexus failure require reconstruction, or can a later live
   activation expose the known wake-classification defect?
2. Do the measured mechanisms require continuing an open workflow to detect them,
   or does ordinary completed-history replay suffice for at least one mechanism?
3. Does the tested selection procedure add detection value over comparably equipped
   conventional tests on the measured cases?
4. Does the proposed live/replay/reconstruction classification identify a new,
   explanatory relationship with meaningful prospective predictions?
5. Is automatic source-to-replay analysis a specified contribution with a concrete
   unresolved obligation, or only an unimplemented possibility?

For each question, record the closest explanation or method, evidence for and
against it, residual uncertainty, and whether another experiment would discriminate
scientifically consequential alternatives. Source inspection is explanatory
evidence, not a causal ablation. Never treat absent experiments as passing results.

## Decision rules

- Reject a necessary-condition claim when an admissible retained counterexample
  violates it. Scope rejection to the claim and fixture actually checked.
- Reject measured superiority on a development set when its declared baseline
  detects the same mechanisms without the claimed disadvantage. Do not infer that
  every future method or larger domain is equally easy.
- A descriptive study needs a defined population, meaningful estimand, sampling
  procedure, and a reason its answer would add knowledge. A taxonomy and more cases
  alone do not pass this gate. Repetitions are not independent mechanisms.
- A predictive study needs a fixed information budget and predictions before
  inspecting held-out fixes/outcomes. None of the inspected cases is a holdout.
- A method/theory proposal needs a defined input, semantics, output, technical
  claim, and explicit comparison with the closest work. Empirical superiority is
  not mandatory for a theoretical or empirical contribution; the claimed advance
  must nevertheless be substantive and supported.
- If no candidate passes, stop expanding this research direction. Preserve the
  evidence and record the failed gate. Do not automatically rename the contribution
  or launch a larger corpus/generator to keep the project moving.

An unexplained anomaly is one valid entry point, not a universal requirement for
science. A precise unresolved theorem, practically significant measurement, or
credible methodological limitation can also qualify. Our earlier conversational
criterion was too restrictive if read as a general definition of science.

## Evidence and literature audit

Recheck the retained 72-trial schedule comparison, 24-trial Nexus context study,
48-trial continuation sweep, and original/corrected 12-trial local-activity studies
with their existing raw-artifact auditors. Derive an audit summary from those
verified records; hash all inputs. Report first-failure activation state separately
from later retries and offline replay. Keep original measurement errors visible.

Revisit primary sources for state identification, crash testing, durable replay
semantics, trace validation, and live updates. Record precise reading scope,
applicability limits, and retrieval failures. This is a focused gap audit, not an
exhaustive systematic review. A formalism's ability to express a problem does not
prove a practical tool solves arbitrary workflow code.

CI validates evidence consistency and documentation, not novelty, causal truth,
or independent review. Fresh CI repetitions of known cases remain validation
repetitions. Report any discrepancy before adopting a final decision.

## Deliverables

- A compact question-by-question decision record with primary-source references.
- A CI-generated machine-readable evidence audit, exact run/commit provenance,
  and preserved output.
- Updated research entry point and status pages; historical proposals explicitly
  marked as superseded where their next steps conflict with the current decision.
- Either a separate frozen discriminating-experiment protocol, or an explicit
  stop decision explaining why no new scientific experiment is justified yet.
