# Comparative evaluation protocol — version 1

[Case study](../../RESEARCH.md) · [Frozen corpus](corpus.json)

## Question and frozen artifact

Do recorded-input TLA+ trace checks detect implementation faults beyond the existing
and expanded behavioral tests, on the same implementation and controlled stimuli?
The artifact baseline is commit `7aa516d13dde8a3f9f4c2d893b34e3e5d6fb9e80`.
The corpus records its source hash and all five suite hashes. The original upstream
baseline is `049e01c9d726ef68bff7be857c735723b9801512`.
This protocol and corpus are committed before running the comparison. Four faults
have known pilot outcomes; two are new boundary-derived faults. This is a transparent
exploratory study, not a blinded benchmark or a statistical estimate of real defects.
Changing a fault, suite, observation, or scoring rule requires a versioned amendment.

## Population and rationale

Six single-edit faults cover denial/remember guarding, tool eligibility, publication
order, malformed superseded results, closure finalization, and evaluator denial.
They are purposively selected from code boundaries, not sampled from all possible
faults. The malformed-result case deliberately tests a model exclusion. No new
production defect is implied by a synthetic fault. Equivalent mutants and uncovered
boundaries must be reported rather than removed after results are known.

## Four approaches and units of comparison

| Approach | Fixed input | Outcome |
| --- | --- | --- |
| Existing tests | Unchanged `tests/harness/test_tool_approvals.py` on the fixed artifact | Assertion detection of a Python fault |
| Expanded tests | Existing suite plus superseded-result regressions and all research tests | Assertion detection of the same Python fault |
| Model checking | Existing 13 configurations, including five abstract faults | Separate abstract-design sensitivity; no inference of Python-fault detection |
| Trace checking | Existing observer scenarios with assertions removed only in isolated collector copies | Rejection of the same Python fault's recorded execution |

The existing and expanded arms stop at the first failing test (`-x`). Detection is
binary, so stopped-suite counts are not coverage totals. Test order remains fixed.
Each arm runs in an isolated package copy with explicit import-provenance checks.
The unchanged implementation must pass both suites and all five selected trace
scenario groups before faults are scored.

The model-checking arm does not consume Python code. Its unchanged specification
cannot detect a Python mutation by itself. We therefore report its five existing
abstract controls separately, with no fabricated one-to-one mutation correspondence.
This distinction is necessary for a fair comparison of methods with different inputs.

## Trace collection and scoring

An AST transformation removes `assert` statements from the two observer test modules
in an isolated copy. All other statements, workflow code, barriers, and concrete
production methods stay unchanged. The collector supplies stimuli and observations,
not a behavioral oracle. The transformation hash is retained. Collector success is
not detection. This preserves trace generation when a behavioral assertion would
otherwise abort before writing evidence.

The five model-covered faults use the fixed corpus scenario; coupled scenarios run
under both registration orders. The malformed-result fault is marked out of scope
without relaxing the valid-input model or awarding a rejection.
For each emitted trace, the pinned TLC checker first searches for a matching witness.
Only completed state-space exhaustion without that witness is a rejection. Parser
errors, unsupported observations, timeouts, stale hashes, missing traces, collector
failures, and setup errors are **inconclusive**, not detections. A coupled fault is
detected if either evidenced registration order is rejected; per-trace outcomes remain
available. A baseline inconclusive result invalidates the experiment.

For pytest, only an exit-1 run with a JUnit assertion failure and no setup/collection
errors counts as detection. Other failures remain inconclusive. Survivors are retained.

## Measures and interpretation

Report detection overlap, unique detections, survivors, out-of-scope and inconclusive
cases, and single-run wall time per arm. Time includes the test/collector/checker
subprocesses, excludes package-copy preparation, and is descriptive rather than a
performance benchmark. Denominators distinguish six testable faults from five
model-covered faults. Report source, suite, corpus, model and tool hashes and runtime
versions. CI retains logs, JUnit records, observations, and TLC witnesses/exhaustion.

Modeling and maintenance effort have not been contemporaneously logged; no numerical
effort claim will be reconstructed from memory. Future effort should be logged when
incurred. The two new faults offer limited additional evidence; an independent fault
corpus is still needed to reduce selection bias.

## Publication decision

A trace-only detection would justify investigation, not automatically novelty. No
unique detections would weaken an added-detection claim but could still support
diagnostic or specification benefits if separately measured. A research submission
requires independent abstraction review, external reproduction, a full comparison
with the closest trace-validation work, and a contribution justified by the results.
These are open gates; local self-review is not independent review.
