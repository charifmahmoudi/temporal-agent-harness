# Transfer mapping: Sabot

2026-10-10, after publishing the transfer policy in fc4f010 and before execution.

Pinned scripts/score_by_operator.py exposes fault_counts(rows). Use its existing
callable for the four perturbations, with scored field recovered and identity
(framework, config, task, operator, seed). No new upstream entry point is invented.
The valid reviewer population excludes non-null excluded and autogen/guardrail.
Read all saved wave-2 rows; independently aggregate n, recovered, union, reacted,
union-and-not-recovered, recovered-and-not-union, flags_anchored. Compare exact
counts against the official callable. Preserve all exclusion categories.

Run documented score_by_operator.py --check. Rebuild saved rows using the official
score_wave2.collect from cellverdict/runresult files and registered seeds, comparing
all row fields by identity. This cross-check is upstream-code consistency, not
independent re-adjudication of model text. Recompute clean false flags with the
official scanner and retain their denominators; do not equate them with faulty
input flags. The independent arithmetic does not rerun a language-model judge.

Apply removal/null to recovered in the first stored row, exact duplication of that
row, and empty rows. Preserve the official pct(0,0) representation to distinguish
zero counts with no population from a zero-percent conclusion.

Original rows, raw traces and published tables stay unchanged; return values and
temporary generated reports are retained in CI artifacts.
