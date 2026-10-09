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
comparison and cancellation reports from their evidence snapshots, including retained
cancellation archive hashes and raw outcomes. It cannot validate scientific truth;
formula fidelity and interpretation still require review. Editable SVG figures are
regenerated from `research/figures/generate.py` when semantics change.

## Work and decision record

| Gate | Current status | Completion criterion |
| --- | --- | --- |
| Stable case-study baseline | Complete: `7aa516d13dde8a3f9f4c2d893b34e3e5d6fb9e80` | Source and suite hashes retained in corpus |
| Comparison protocol | Frozen before execution | Versioned corpus and scoring rules |
| Comparative measurement | See current evaluation report | Valid baseline and all planned arms reported, including errors |
| Cancellation lifecycle study | Complete for the declared one-call experiment; isolated correction prepared | Six expected TLC checks, both 23-test variants, retained histories and replay outcomes |
| Cross-version replay | Complete for the declared offline probe: local and CI outcomes agree | 64 cells plus paired observer-free controls; separate local and CI archives retained and checked |
| Activity-backed upgrade | Complete for the declared one-activity and nonsticky replacement experiment | 12 fresh executions, 36 replay cells, eight live cases, and 375 versioned harness regressions; raw histories and ledger checked |
| Independent abstraction review | Outstanding | External review addressing correspondence and atomicity |
| External reproduction | Outstanding | Independent environment and retained categorical results |
| Upstream feedback | Prepared, not submitted | Explicitly authorized submission and recorded maintainer response |
| Novelty assessment | Focused claim comparison complete; novelty unestablished | Independent assessment and resolution of remaining literature gaps; a justified contribution |
| Publication decision | Open | Evidence supports chosen claim and submission category |

Future effort logs should record task, date, contributor, elapsed effort, and artifact
or issue link. Historical modeling effort was not recorded and must not be invented.

The upgrade report is generated from a retained local evidence archive. Documentation
CI checks its hashes, cell inventory, control results, and application comparisons.
Keep local measurement distinct from a CI run; do not update the recorded execution
commit to a later documentation-only commit.

The activity report is independently generated from its retained CI archive. Its
check validates exact case inventories, replay classifications, raw server-event
counts, ledger records, patch-marker identity, source hashes, and regression JUnit.
New migration cohorts or retry/routing assumptions require a new protocol; do not
extend the B → V result to untested histories or overwrite the measured C → V failures.


## Review handoff and prospective work

The [review quickstart](evaluation/review-quickstart.md) pins subject `ccb7499` and
separates retained-evidence auditing, fresh TLC execution, and fresh implementation
runs. The driver was smoke-tested by the author; this is not external reproduction.
The [invitation](evaluation/review-invitation.md) remains unsent, recipient unselected.
Only an actual reviewer response can close the independent-review gates.

The [novelty review](evaluation/novelty-review.md) rejects claims of a new tracing or
versioning method. [Second-case execution](evaluation/prospective-case.md) is deferred
until a qualifying candidate and pre-execution predictions are recorded. A hand-built
repeat of documented SDK behavior does not meet that gate.


The comparison and workflow-local upgrade reproduction jobs explicitly use subject
`ccb74997404f6b9fd9f5654ac5a441337581d673`; their current-scoring jobs use the PR revision.
This separation was introduced after the F02 docstring clarification tripped their
full-source byte guards. The guards and frozen protocols remain intact. Current-code
verification is provided by the other model, trace, harness, cancellation, and activity
jobs. Report the subject commit for a reproduction, not merely the triggering PR head.
