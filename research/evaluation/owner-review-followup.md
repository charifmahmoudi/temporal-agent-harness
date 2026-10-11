# Response to extended owner review: F04 and F05

[Review comment](https://github.com/charifmahmoudi/temporal-agent-harness/issues/2#issuecomment-6088900573) · [Earlier response](owner-review-response.md) · [Quickstart](review-quickstart.md)

All R01–R14 now have scoped review verdicts. The extended AI-assisted review accepts
F01–F03 and requests revisions for F04/F05. It is not independent human validation,
maintainer confirmation of the cancellation contract, or approval to close the issue.

| Finding | Change | Verification | Status |
| --- | --- | --- | --- |
| F04 / R11 | Explicit Python paths become absolute without resolving executable symlinks; the default path uses the same selection function | A real symlinked venv, a module installed only in it, and explicit/default CLI plans for both live stages yield the same interpreter, `sys.prefix`, and dependency | Addressed; awaiting review confirmation |
| F05 / R07, R08 | Projector and live study assertions share single-call audit checks: dispatch call identity, correlated evaluation ID/evaluator, and exactly one superseded terminal across ended/superseded/error | All four retained cancellation records and twelve fresh-activity records pass; unrelated tool/evaluation IDs and extra ended/error terminals fail; both extra payloads validate against their actual Pydantic classes | Addressed; awaiting review confirmation |

## What was run in this follow-up

- Seven focused regression tests in `tests/evaluation/test_review_followup.py`, plus
  three existing activity-scoring tests: **10 passed**. The venv test runs generated
  interpreter paths, not just string comparisons.
- Existing baseline helper boundary tests: **7 passed**.
- Cleanup correspondence: **4 witnesses, 8 model rejections, 7 projection rejections**.
  The four additional controls cover both identity gaps and duplicate ended/error
  terminals. These are pre-TLC integrity checks, not additional TLA+ properties.
- History: **12 expected results**, including agreement with all **36 retained cells**.
- Documentation/archive consistency and executable source mapping are checked before
  publication. Implementation source and the original implementation archives are
  unchanged by these fixes.

The refreshed [model evidence](model-bridges.md) retains current checker/helper
hashes and TLC logs. The [original bridge snapshot](model-bridges-v1.json.gz) remains
available with its old checker and three projection controls. The cancellation,
activity, and comparison archives have not been replaced. This follow-up reuses
retained implementation observations; it is not fresh live reproduction.

The [measured activity runner](activity-runner-v1.py) is retained byte-for-byte and
checked against the original archive's runner hash. The current runner adds the
stronger audit assertion; the renderer verifies that its history projection and
scenario constants still equal the measured runner's AST. It also applies the new
audit check to all twelve retained fresh records. This separates frozen provenance
from current validation without weakening the archived hash guard.

The original review subject stays at `ccb74997404f6b9fd9f5654ac5a441337581d673`.
The corrected driver still runs that subject's scripts. Therefore its frozen model
stage still expects **three** projection rejections. The current branch's checker
expects **seven**. Reviewing F05 requires the current follow-up checker/tests;
rerunning the original subject alone cannot validate a later checker change.

## CI evidence and limits

At preceding revision `b43c05e218d3ab4ab099956f66d1f46270ddb951`, all seven research/UI/codegen
workflows passed, including live cancellation and activity studies. These are author
CI runs, separate from the reviewer's locally blocked live attempts. They do not
retroactively complete the reviewer's reproduction record or validate this new
assertion code before its own CI runs.

The general Tests workflow failed on Python 3.13 (929 passed, 1 failed):
`tests/examples/monty/test_code_mode_vfs_e2e.py::test_a_host_call_made_before_a_file_operation_still_resolves`
observed `fs_read` before `add`. The result itself was correct; the ordering assertion
failed. [Failure log](https://github.com/charifmahmoudi/temporal-agent-harness/actions/runs/37988075279/job/114015064569).
Python 3.11, 3.12, and 3.14 passed. Its cause has not been established; this response
does not dismiss it as a flake, alter that assertion, or count the whole suite green.

Current cancellation/activity CI runs the strengthened audit assertions and C/V
regressions. CI outcomes are recorded in the issue follow-up, separately from local
checks. Independent human review, maintainer contract confirmation, fresh reviewer
live reproduction, and a defensible publication-novelty assessment remain open.

## Story and decision

The cancellation witness and the replay findings still stand within their stated
bounds. The review exposed weaknesses in the reproduction wrapper and in which
concrete observations the model bridge trusted; it did not show that the retained
real traces were corrupt. The bridge is stronger after these fixes, but remains
manual, retrospective, and limited to the observed completing cases.

Please confirm F04 and F05 using their IDs or give a counterexample. Leave the issue
open until the owner explicitly decides to close it. Do not treat accepted scoped
R-item verdicts as independent validation, a novelty decision, or universal correctness.
