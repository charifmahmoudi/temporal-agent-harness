# Response to owner review F01–F03

[Issue #2](https://github.com/charifmahmoudi/temporal-agent-harness/issues/2) · [Original review](https://github.com/charifmahmoudi/temporal-agent-harness/issues/2#issuecomment-6088725189) · [Validation record](owner-review-response.json)

The input is an AI-assisted static review posted on the owner's behalf. It is not
independent human validation or fresh implementation reproduction. This response
addresses only F01–F03; it does not change the other R-item verdicts or close the issue.

| Finding | Interpretation | Change | Validation | Status |
| --- | --- | --- | --- | --- |
| F01 / R11 | Recording a moving branch's HEAD does not enforce the stated driver pin | Quickstart now checks out driver `f152a9787292ff8ccfba204c0a892cc5555f6e46` detached and explicitly verifies it and subject `ccb74997404f6b9fd9f5654ac5a441337581d673` | Fresh remote clone; both HEADs checked; pinned driver plan and audit completed | Addressed; awaiting owner confirmation |
| F02 / R03 | Exception type does not identify whose cancellation is caught | Baseline helper docstring explicitly distinguishes child, awaiting caller, and whole-workflow scope and describes the known caller limitation | Complete source AST comparison after removing only the helper docstring is equal; mapped-source check passes | Addressed; awaiting owner confirmation |
| F03 / R08 | Original-upstream patch was linked as though it matched the frozen research source | Added a source-only direct patch generated against the frozen research subject; documented exact bases and retained the historical patch | `git apply --check` and application pass on a separate pinned worktree; resulting bytes equal the preparer's output and retained corrected-source hash; type guard remains | Addressed; awaiting owner confirmation |

## Follow-up artifacts

- [Updated quickstart](review-quickstart.md).
- [Helper explanation](../../temporal_agent_harness/harness/agent_workflow.py), `_cancel_and_settle`.
- [Frozen-research direct patch](../upstream/caller-cancellation-research.patch).
- [Patch/base correspondence and scope](../upstream/caller-cancellation.md).

The research patch targets the frozen subject, so its context retains that revision's
old docstring. The follow-up source clarifies the docstring separately; neither
historical source nor measured archives were rewritten. The historical upstream patch
still targets `049e01c9d726ef68bff7be857c735723b9801512` and includes its seven standalone
regressions. It is not a diff against the review subject.

## Validation scope

The author followed the updated detached-checkout and separate-worktree steps using
a fresh remote clone. Both exact revisions were verified before plan/audit execution.
Only the standard-library audit was run; dependency installation, fresh TLC, and live
Temporal reproduction stages were not needed for these static fixes and were not run
as part of this local follow-up. This does not substitute for the reviewer's unrun
stages. The JSON record preserves audit logs, runtime metadata, and resulting hashes.

F03's resulting source SHA-256 is
`eb887d8c3b996c91f0171c72b1beda3505c13c60f612b979fe238a37b2dddc9d`, exactly the
corrected-source hash in the retained cancellation-study snapshot. This is byte
correspondence evidence, not a new runtime experiment.

The current documentation consistency check and mapped executable-source check also
pass. No new whole-workflow cancellation guarantee, contract acceptance, novelty,
or universal refinement claim is introduced.

## Decision requested from the owner

Confirm whether the three responses address your concerns, or add a follow-up using
the same F ID. R02, R04–R07, R09–R10, and R12–R14 remain not reviewed in the original
review record. R03/R08/R11 remain scoped findings, not full acceptance of those areas.
The issue stays open until you explicitly confirm closure.


## CI follow-up: preserve the historical subject

The docstring-only edit correctly tripped byte-level source guards in the historical
[comparison run](https://github.com/charifmahmoudi/temporal-agent-harness/actions/runs/37987851266)
and [cross-version replay run](https://github.com/charifmahmoudi/temporal-agent-harness/actions/runs/37987851174).
Those failures are retained as provenance failures, not model or runtime findings.

The two workflow reproduction jobs now explicitly check out frozen subject
`ccb74997404f6b9fd9f5654ac5a441337581d673`, including its protocol and scripts.
Separate scoring-control jobs check out the current PR revision. Source hash guards,
frozen corpora, and recorded evidence remain unchanged. Current model/trace, harness,
cancellation, and activity jobs continue to run the current revision. A historical
reproduction pass must not be reported as testing current implementation bytes.
