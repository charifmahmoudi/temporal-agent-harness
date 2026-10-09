# Evidence and reproduction

[Case study](../RESEARCH.md) · [Properties](properties.md) · [Correspondence](correspondence.md)

## Validated revision

[Verification run 37885725766](https://github.com/charifmahmoudi/temporal-agent-harness/actions/runs/37885725766)
passed for `d3c3f9b3c6c45cd2a6d8afbda4f6dcc2f75c0f1d`. This revision includes both
schema-2 input-constrained checkers. Later documentation changes do not change those
results. Each fresh run records its own exact commit and source/module hashes.

| Experiment | Result | What it supports |
| --- | --- | --- |
| Selected Python/Temporal tests | 82 passed | Assertions for controlled behavior and the malformed-result fix |
| TLC configurations | 13 expected results | Finite safety, conditional progress, and fault sensitivity |
| Implementation traces | 31 matched | Recorded inputs and partial states admit legal model executions |
| Fabricated invalid traces | 8 rejected | Selected impossible observations/inputs are not accepted |
| Isolated Python faults | 4 detected | Selected regressions fail for their intended code edits |

The complete repository matrix also passed on Python 3.11–3.14 for the preceding fixed
revision `128af56bc2b904aa4929b604824fb8d397ff6c62`;
[its Python 3.12 job](https://github.com/charifmahmoudi/temporal-agent-harness/actions/runs/37885395560)
reported 889 passing tests. These totals are not schedule-coverage percentages.

## Model configuration inventory

| Model | Normal safety | Conditional progress | Synthetic faults |
| --- | --- | --- | --- |
| Approval | Safety; TwoCalls | Liveness | Overwrite; Bypass |
| Cascade | SameTool; DifferentTools; SameToolReverse; DifferentToolsReverse | Liveness | LeakScope; OverwriteSettled; ReverseCause |

This gives six safety configurations, two progress configurations, and five fault
configurations. Reverse-order configurations are generated from their base templates.
No reachable-state constraint is used to prune the normal checks.

## Controlled execution coverage

Seven single-call scenarios exercise human approval/denial, evaluator approval/denial,
closure, delayed cancellation cleanup, and completion/readiness competing with approval.
Twelve coupled scenarios each run under a,b and b,a registration order:

| Scenarios | Boundary exercised |
| --- | --- |
| remember_first; evaluator_deny_first; human_deny_first | Resolution precedence |
| denied_remember; different_tool | Remember eligibility and isolation |
| policy_relax; tighten_after_release | Pending release and restriction during delayed cleanup |
| close_first; remember_then_close | Internal non-suspending closure/approval orderings |
| evaluator_approve_first; evaluator_escalate_first; evaluator_error_first | Completed evaluator outcomes before remember |

Barriers establish readiness and cleanup order; elapsed time is not used to infer a
race winner. Closure variants control internal operations, not independent network
request placement. A separate malformed-superseded-result Temporal experiment tests
the robustness fix and is not represented as a valid-input model trace.

## Controls and retained artifacts

Single-call invalid controls reject denied dispatch, decision reversal, and approval
without a recorded input. Coupled controls also test overwritten denial, invented
policy, wrong initiating cause, and wrong decision input: five coupled controls total.

Python mutations remove denial/remember guarding, leak tool scope, reverse publication,
and remove superseded-result type validation. Each runs in an isolated copy with
import provenance checked. The seven-test isolated baseline must pass; faults must
produce assertion failures without collection/setup errors.

CI retains TLC logs and hashes, raw events, projected states, generated trace modules,
witness/rejection logs, mutation logs, and JUnit XML. Historical schema-1 traces allowed
broader hidden actions and are not evidence for the stronger schema-2 criterion.

## Reproduce

Use Java 17 and Python 3.12. TLA+ tools v1.8.0 is pinned; the scripts verify SHA-256
`7beec0f04818732a62fa193731711a99aa4f11279499b2360a7d156c519ea78d`.

```bash
uv sync --frozen
curl --fail --location --retry 3 --retry-all-errors \
  https://github.com/tlaplus/tlaplus/releases/download/v1.8.0/tla2tools.jar \
  -o tla2tools.jar
python research/scripts/check_source.py
python research/scripts/check_model.py --jar tla2tools.jar
python research/scripts/check_cascade.py --jar tla2tools.jar
uv run --frozen pytest tests/harness/test_tool_approvals.py \
  tests/harness/test_auto_mode_superseded_result.py tests/research/ -q
uv run --frozen python research/scripts/check_traces.py --jar tla2tools.jar
uv run --frozen python research/scripts/check_cascade_traces.py --jar tla2tools.jar
uv run --frozen python research/scripts/check_implementation_mutations.py
```

Use a clean checkout or remove stale generated trace output before regeneration.
Temporal experiments require the SDK's time-skipping test server. Tool failures,
missing evidence, stale hashes, unsupported fields, and timeouts fail verification.
The [workflow](../.github/workflows/verification.yml) is the executable reproduction
reference; figure sources are regenerated with `python research/figures/generate.py`.
