# Comparative evaluation — results v1

[Case study](../../RESEARCH.md) · [Protocol](protocol.md) · [Evidence snapshot](results-v1.json)

This report is generated from the committed JSON snapshot; edit interpretation
in [Assessment](assessment.md), not the measurements here.

Execution commit: `a61ba1293f4c58586c10833073ab8a9f4d2b5e42`.
Artifact baseline: `7aa516d13dde8a3f9f4c2d893b34e3e5d6fb9e80`.
Corpus SHA-256: `a18662cb771a99510da1d3ba831b7f9546cce2a474c8bfe2b13cb5ddf17e411e`.
[CI evidence](https://github.com/charifmahmoudi/temporal-agent-harness/actions/runs/37889321814).

## Detection matrix

| Python implementation | Existing tests | Expanded tests | Recorded-input trace checking |
| --- | --- | --- | --- |
| baseline | survived | survived | survived |
| denial_remember | survived | detected | inconclusive |
| scope_leak | survived | detected | inconclusive |
| reverse_publication | survived | detected | detected |
| unvalidated_superseded | survived | inconclusive | out of scope |
| close_approves | detected | detected | detected |
| evaluator_deny_approves | detected | detected | detected |

The baseline must survive all arms. “Detected” means a valid assertion failure
or completed TLC rejection. “Inconclusive” is not detection or survival.
“Out of scope” preserves the model exclusion.

## Totals

| Arm | Detected | Survived | Inconclusive | Out of scope |
| --- | --- | --- | --- | --- |
| existing | 2 | 4 | 0 | 0 |
| expanded | 5 | 0 | 1 | 0 |
| trace | 3 | 0 | 2 | 1 |

Trace-only detections with both test arms successfully surviving: **none**.

This comparison has six Python faults; five have a model-covered trace arm.
The unchanged model does not consume Python mutations. The separate model
experiment has 13 configurations and five abstract-fault controls; those
are not Python-fault detections in this matrix.

## Single-run wall times

| Fault | Existing tests (s) | Expanded tests (s) | Collector + TLC (s) |
| --- | --- | --- | --- |
| denial_remember | 5.43 | 7.52 | 1.92 |
| scope_leak | 5.42 | 8.50 | 1.90 |
| reverse_publication | 5.47 | 7.84 | 3.12 |
| unvalidated_superseded | 5.38 | 5.44 | — |
| close_approves | 5.27 | 5.26 | 2.36 |
| evaluator_deny_approves | 3.57 | 3.58 | 2.38 |

Times include subprocess execution and exclude package-copy preparation.
They are one observation on one runner, not a performance benchmark.
The JSON retains per-trace outcomes, counts, runtime versions, and hashes.
Raw logs and JUnit evidence remain in the linked CI artifact.
