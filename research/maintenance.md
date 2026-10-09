# Maintaining the scientific artifact

[Case study](../RESEARCH.md) · [Evaluation protocol](evaluation/protocol.md)

Documentation changes accompany the implementation or experiment that makes them
necessary. This policy applies to future contributions; it does not imply unattended
monitoring or automatic literature review.

| Change | Required documentation and verification |
| --- | --- |
| Production approval behavior | Mapping-impact review, model/contract assessment, affected regressions and source guard |
| Model state, action, or atomicity | Model guide, property catalogue, correspondence, and affected figures; TLC checks |
| Trace schema or instrumentation | Correspondence and evidence definitions; positive and negative controls |
| Comparative suite, fault, or scoring | Versioned protocol amendment and new corpus; retain preceding results |
| New measured result | Exact commit/run, machine-readable record, generated report, interpretation and limitations |
| New research claim | Primary-source comparison and explicit supporting evidence |
| External review or upstream response | Linked record, actual feedback, status update; no self-review substitution |

Model and trace controls test selected failure modes. Never silently replace an
inconclusive result with detection, or infer implementation proof from passing TLC.
Prior results remain tied to their original revisions.

The documentation check validates relative links and regenerates the committed
comparison report from its evidence snapshot. It cannot validate scientific truth;
formula fidelity and interpretation still require review. Editable SVG figures are
regenerated from `research/figures/generate.py` when semantics change.

## Work and decision record

| Gate | Current status | Completion criterion |
| --- | --- | --- |
| Stable case-study baseline | Complete: `7aa516d13dde8a3f9f4c2d893b34e3e5d6fb9e80` | Source and suite hashes retained in corpus |
| Comparison protocol | Frozen before execution | Versioned corpus and scoring rules |
| Comparative measurement | See current evaluation report | Valid baseline and all planned arms reported, including errors |
| Independent abstraction review | Outstanding | External review addressing correspondence and atomicity |
| External reproduction | Outstanding | Independent environment and retained categorical results |
| Upstream feedback | Prepared, not submitted | Explicitly authorized submission and recorded maintainer response |
| Novelty assessment | Incomplete | Full closest-work comparison plus a justified contribution |
| Publication decision | Open | Evidence supports chosen claim and submission category |

Future effort logs should record task, date, contributor, elapsed effort, and artifact
or issue link. Historical modeling effort was not recorded and must not be invented.
