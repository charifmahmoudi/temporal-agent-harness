# Owner review issue draft

Status: created as [issue #2](https://github.com/charifmahmoudi/temporal-agent-harness/issues/2).
The body below is the original template; live verdicts and follow-up responses are recorded in the issue.
Intended assignee: `charifmahmoudi`.
Intended title: Review the cancellation case study: clarity, model–code correspondence, evidence, and research claims.

## Purpose and review scope

Review the case study in [PR #1](https://github.com/charifmahmoudi/temporal-agent-harness/pull/1) and leave feedback that can be converted into specific documentation changes, code/model fixes, verification work, or decisions about the research claim.

**You do not need to approve the work or understand TLA+ before starting.** “I cannot follow this step” is a useful finding. You may review one section at a time and reply in ordinary language.

This issue records your project review. Record your involvement and any assistance below; completing it does not automatically establish independent external validation.

### Frozen versions

- **Code, models, and measured evidence under review:** `ccb74997404f6b9fd9f5654ac5a441337581d673`.
- **Review instructions, literature assessment, and driver:** `f152a9787292ff8ccfba204c0a892cc5555f6e46`.
- The links below are pinned, so later changes will not silently alter what you reviewed.
- Model and implementation experiments passed author CI for the subject revision. That is a starting point to challenge, not a reason to accept the claims.

## The story you are evaluating

1. A human approves a tool call while its evaluator is still running.
2. The harness cancels that evaluator and waits for cleanup.
3. The caller itself is cancelled during this wait. The studied contract says the invocation should stop while the accepted approval remains recorded.
4. The baseline can swallow this cancellation and dispatch the tool.
5. A direct correction stops the tested new invocations, but may conflict with activity commands already recorded by the old workflow.
6. A versioned correction preserves the tested baseline histories, with documented limitations for other histories.

**Review whether this story is understandable, intended, faithfully modeled, and supported by the evidence.** The larger question is whether the case teaches something useful beyond established cancellation and workflow-versioning practice.

### Short glossary

| Term | Meaning here |
| --- | --- |
| Model | A smaller, manually written description of relevant states and possible steps |
| Property | A rule the modeled behavior should satisfy |
| TLC | The tool that explores the finite TLA+ model and can produce a violating execution |
| Trace check | Whether recorded implementation inputs and observations fit an execution of the model |
| Replay | Running workflow code against recorded durable history to check command compatibility |
| B / C / V | Baseline / direct correction / versioned correction |

## How to leave actionable feedback

**Checking a box means you reviewed the item and recorded a verdict; it does not mean you agree.**

For each item use one verdict: **accept**, **change needed**, **unclear**, or **not reviewed**. Add the item ID, a location, and your reason. Partial reviews are welcome.

Copy this block into a comment for each finding, or combine several findings in one comment:

```text
Finding: F01
Review item: R01
Verdict: unclear
Importance: blocking / important / minor / question
Location: file + heading, function, property, or quoted sentence
What I understand or observed:
What is unclear, wrong, missing, or unsupported:
Expected behavior or suggested change (optional):
Evidence: example sequence, source link, command/output, or reasoning
Question or decision I need answered:
```

If you have only a question, the ID and question are enough. **Do not invent evidence or a proposed solution to complete the template.** Number findings F01, F02, etc.; keep the R IDs below so subsequent work can link back to your input.

## Pass 1 — Understand the story and intended behavior

Start with the [one-call walkthrough](https://github.com/charifmahmoudi/temporal-agent-harness/blob/f152a9787292ff8ccfba204c0a892cc5555f6e46/research/walkthrough.md), then the [storyline](https://github.com/charifmahmoudi/temporal-agent-harness/blob/f152a9787292ff8ccfba204c0a892cc5555f6e46/research/storyline.md). This pass does not require running anything.

- [ ] **R01 — Can I explain the problem?** In two or three sentences, explain what goes wrong, what the repair changes, and why durable history matters. Identify the first paragraph or transition you cannot explain.
- [ ] **R02 — Is the cancellation contract right?** Should an approved invocation stop when its caller is cancelled during evaluator cleanup? Should the accepted approval remain recorded? Give a scenario that supports or challenges this policy. Distinguish caller-task cancellation, cancelling the evaluator child, session closure, and whole-workflow cancellation.
- [ ] **R03 — Is the documentation clear and consistent?** Can you distinguish what was discovered by inspection, checked in a model, reproduced in Python, and tested through replay? Flag unexplained terms, inconsistent claims, or places where “dispatch” could mean either gate permission, an activity command, or an external effect.

**Useful output:** one short explanation in your own words and any F-numbered questions. If this pass is unclear, report that before spending time on formal details.

## Pass 2 — Challenge the model and its link to code

Read [code correspondence](https://github.com/charifmahmoudi/temporal-agent-harness/blob/f152a9787292ff8ccfba204c0a892cc5555f6e46/research/correspondence.md), [Cleanup model guide](https://github.com/charifmahmoudi/temporal-agent-harness/blob/f152a9787292ff8ccfba204c0a892cc5555f6e46/research/models/cancellation/README.md), and the [property catalogue](https://github.com/charifmahmoudi/temporal-agent-harness/blob/f152a9787292ff8ccfba204c0a892cc5555f6e46/research/properties.md).

Concrete reference files: [production Python](https://github.com/charifmahmoudi/temporal-agent-harness/blob/ccb74997404f6b9fd9f5654ac5a441337581d673/temporal_agent_harness/harness/agent_workflow.py), [Cleanup.tla](https://github.com/charifmahmoudi/temporal-agent-harness/blob/ccb74997404f6b9fd9f5654ac5a441337581d673/research/models/cancellation/Cleanup.tla), and [trace checker](https://github.com/charifmahmoudi/temporal-agent-harness/blob/ccb74997404f6b9fd9f5654ac5a441337581d673/research/scripts/check_cleanup_traces.py).

- [ ] **R04 — Does the five-state example match the source?** Follow `_handle_tool_approval`, the settled branch of `_run_auto_mode_evaluator`, `_cancel_and_settle`, and the tool gate/dispatcher. Check whether each claimed model step corresponds to the described code boundary. Identify any omitted suspension or competing action.
- [ ] **R05 — Do the properties protect the right things?** Explain why `AuthorizedDispatch` can hold while `CallerCancellationRespected` fails. Challenge a property that is too weak, too strong, or unrelated to intended behavior. Do not treat permission as a guarantee that an invocation must execute.
- [ ] **R06 — Are the assumptions defensible?** Inspect `CancelCaller`, which includes the child's completing response, and the conditional cleanup-progress claim. Consider a child that never finishes, a task already done, or cancellation at another point. Does the documentation distinguish unsupported cases from guarantees?
- [ ] **R07 — Is the trace bridge strict enough?** Check how recorded approval, pending cleanup, caller cancellation, and final outcome constrain TLC. Only consumption, cleanup completion, and finalization may be hidden. Can you describe an impossible concrete sequence that might nevertheless pass, or a legitimate sequence it rejects? Review the four matches and rejection controls without interpreting them as universal refinement.

**Useful output:** cite the exact function/action/property. A proposed event order in plain language is sufficient; a formal counterexample is optional.

## Pass 3 — Challenge the repair and upgrade result

Read the [activity results](https://github.com/charifmahmoudi/temporal-agent-harness/blob/f152a9787292ff8ccfba204c0a892cc5555f6e46/research/evaluation/activity-results.md), [History model guide](https://github.com/charifmahmoudi/temporal-agent-harness/blob/f152a9787292ff8ccfba204c0a892cc5555f6e46/research/models/history/README.md), and [model-connection results](https://github.com/charifmahmoudi/temporal-agent-harness/blob/f152a9787292ff8ccfba204c0a892cc5555f6e46/research/evaluation/model-bridges.md).

Patch references: [direct correction](https://github.com/charifmahmoudi/temporal-agent-harness/blob/ccb74997404f6b9fd9f5654ac5a441337581d673/research/upstream/caller-cancellation.patch) and [versioned correction](https://github.com/charifmahmoudi/temporal-agent-harness/blob/ccb74997404f6b9fd9f5654ac5a441337581d673/research/upstream/caller-cancellation-versioned.patch). These corrections are isolated experiment patches, not applied to production source on this branch.

- [ ] **R08 — Does the repair address both child responses?** Check a child that re-raises the second cancellation and one that returns normally. Does the caller cancellation propagate while accepted approval and the tested evaluation audit record remain consistent? Identify any unsupported claim about other cancellation paths.
- [ ] **R09 — Are history compatibility and effects distinguished correctly?** Inspect B → C incompatibility, B → V compatibility, and the C → V limitations. Check that an old ledger write is preserved rather than claimed to be undone, and that the live failure is described as workflow-task nondeterminism, not automatically terminal workflow failure.
- [ ] **R10 — Is the History abstraction adequate?** Challenge its command/marker rules and one-successful-attempt effect assumption. Does agreement with 36 already-known replay cells justify only retrospective consistency? Are missing retries, partial histories, routing, and the lack of a formal composition with Cleanup disclosed clearly?

**Useful output:** identify the precise B/C/V direction and whether your concern is about fresh execution, replay, live replacement, or external effect.

## Pass 4 — Reproduce what you choose to check

Use the [pinned quickstart](https://github.com/charifmahmoudi/temporal-agent-harness/blob/f152a9787292ff8ccfba204c0a892cc5555f6e46/research/evaluation/review-quickstart.md) and [review driver](https://github.com/charifmahmoudi/temporal-agent-harness/blob/f152a9787292ff8ccfba204c0a892cc5555f6e46/research/scripts/reproduce_review.py). Follow its setup in a disposable environment. When checking out `review-tools`, use the pinned instructions revision `f152a9787292ff8ccfba204c0a892cc5555f6e46`; the separate `review-subject` stays at `ccb74997404f6b9fd9f5654ac5a441337581d673`.

You can start with the audit stage and report the other stages as not run.

| Stage | What it does | Main expected result |
| --- | --- | --- |
| `audit` | Checks retained archives, documentation, and source mapping | Consistency checks complete; this does not generate new implementation evidence |
| `models` | Runs the finite models and trace checks | Cleanup: six expected configurations; bridge: four matches, eight model rejections, three malformed-record rejections; History: twelve expected outcomes |
| `cancellation` | Runs B/C cancellation scenarios and their replays | 23 tests per variant, 16 completed-history replays per variant, 375 C harness regressions |
| `activity` | Runs fresh activities, replay cells, replacements, V regressions | 12 fresh runs; 36 cells: 26 compatible / 10 explicit nondeterminism; eight live cases; 375 V regressions |

- [ ] **R11 — Record the scope actually attempted.** Record environment, subject/driver revisions, commands, assistance, and each stage as passed, failed, inconclusive, or not run.
- [ ] **R12 — Compare actual outcomes and retain failures.** Link logs, summaries, histories, and ledger evidence for any discrepancy. Do not count timeouts or missing executables as semantic findings. Preserve failures and run-specific hashes instead of replacing the frozen archives.

Some model failures are **expected counterexamples**; baseline characterization tests can pass by reproducing the defect. A green suite does not mean the baseline satisfies cancellation respect. New history IDs and hashes may differ; compare the defined categories and source provenance.

Copy this execution record into a comment:

```text
Reviewer / date:
Prior involvement and assistance:
Subject commit:
Driver commit:
OS / Python / Java / SDK / lock hash:

audit: passed / failed / inconclusive / not run
models: passed / failed / inconclusive / not run
cancellation: passed / failed / inconclusive / not run
activity: passed / failed / inconclusive / not run

Exact commands:
Evidence links or attachments:
Observed differences:
Setup interventions:
```

## Pass 5 — Assess the research claim and next decision

Read the [claim-by-claim literature comparison](https://github.com/charifmahmoudi/temporal-agent-harness/blob/f152a9787292ff8ccfba204c0a892cc5555f6e46/research/evaluation/novelty-review.md) and [prospective second-case protocol](https://github.com/charifmahmoudi/temporal-agent-harness/blob/f152a9787292ff8ccfba204c0a892cc5555f6e46/research/evaluation/prospective-case.md).

- [ ] **R13 — Is the contribution stated honestly?** Which specific insight is useful? Is it already covered by a closer source? Check that we do not claim a new tracing/versioning method, model-led discovery, universal correctness, or superiority over tests. The frozen comparison found no trace-only detection beyond both test arms.
- [ ] **R14 — What should happen next?** Choose and explain: revise this case; seek another external reviewer; prepare an experience-report draft; or select a qualifying prospective second case. If proposing another case, identify the question it could falsify—not just another opportunity to reproduce known SDK behavior.

## How your input will be used

When you ask me to process this issue, I will read the body and all review comments and:

1. Preserve your finding IDs and distinguish questions, disputed contracts, defects, documentation gaps, and requests for new evidence.
2. Create a response table with **finding → interpretation → action → validation → commit/issue → status**.
3. Fix clear documentation/code/checker issues and run the checks relevant to the change.
4. Ask a focused question where your intended behavior is ambiguous rather than silently choosing a contract.
5. Keep disputed or unsupported claims open; never convert “not reviewed” or silence into acceptance.
6. Report what changed and what still needs your judgment. Repairs do not retroactively alter frozen results.

This is a handoff process, not background monitoring. After commenting, tell me **“Process my review in this issue.”**

## Completion criteria

- [ ] Every R item has a verdict, including explicit “not reviewed” where appropriate.
- [ ] Every attempted execution stage has an outcome and evidence or an explained limitation.
- [ ] Each blocking finding has a linked response, fix, or documented unresolved disagreement.
- [ ] A short final decision states which claims you accept and which remain unsupported.
- [ ] You confirm closure after reviewing the responses. Passing checks alone will not close this issue.

### Final decision template

```text
Overall: ready for the next step / revisions required / cannot assess yet
Claims I accept:
Claims I dispute or cannot assess:
Blocking findings:
Review scopes I did not cover:
Recommended next step:
```

