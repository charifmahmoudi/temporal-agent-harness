# Preserve settled gates when a superseded evaluator returns invalid output

## Problem and proposed behavior

`_run_auto_mode_evaluator` validates ordinary evaluator results, but the settled-first
branch reads `task.result().verdict` before validating the result type. If completion
and settlement are both observable and a custom evaluator returned `None`, a dict, or
a string, that read raises `AttributeError`. The approval entry remains settled, but
the gate aborts instead of reaching normal finalization and the evaluation terminal
event is not published. This is a robustness and audit-completeness defect, not an
observed authorization bypass.

The proposed fix validates `AutoApprovalDecision` before reading its verdict on the
superseded path. Malformed superseded output contributes no verdict metadata; the
already accepted resolution stands and the bracket closes as superseded. The ordinary
invalid-result path continues to emit an error and leave the human gate pending.

## Reproduction and evidence

The baseline under study is `049e01c9d726ef68bff7be857c735723b9801512`. The same unvalidated
read was present in upstream main when inspected on 2026-10-09; this observation is
not a claim about later revisions.

A method-boundary reproducer forces the evaluator task to become done, then approves,
denies, or closes before the runner resumes. Before the fix, all nine combinations of
three invalid values with those competitors raise `AttributeError`; three ordinary
invalid-result cases correctly escalate. After the fix, all twelve pass. The shim
controls this branch and is not a Temporal scheduling emulator.

A separate actual Temporal experiment has the custom evaluator invoke the accepted
approval handler immediately before returning invalid output. This establishes both
conditions in one non-suspending interval. It exercises the concrete branch without
claiming that independent client requests can reliably force the same ordering.
The regression requires successful caller dispatch and two superseded evaluation
terminals. An isolated mutation removes the type guard to check detection on the real
Temporal experiment. CI retains its raw events, JUnit evidence, and mutation logs.

The fixed implementation and the isolated defective variant were exercised in
[CI run 37885395663](https://github.com/charifmahmoudi/temporal-agent-harness/actions/runs/37885395663),
commit `128af56bc2b904aa4929b604824fb8d397ff6c62`. The fixed real Temporal test passed;
removing only the type guard made that same test fail by assertion, without a setup
error. All twelve standalone regressions passed. The patch was independently applied
to a clean baseline checkout and those twelve tests passed there as well.

## Minimal contribution

[superseded-result.patch](superseded-result.patch) contains only the production guard
and twelve standalone regression cases under `tests/harness/`. It applies to the
pinned baseline; the larger research infrastructure is not required to use that patch.

```bash
git apply --check research/upstream/superseded-result.patch
# Apply from a checkout of the baseline, then:
uv run --frozen pytest tests/harness/test_auto_mode_superseded_result.py -q
```

The production change preserves all valid evaluator outcomes. It does not add policy,
change precedence, require an evaluator retry, or suppress an exception from a running
evaluator. The source-map review records that the valid-input TLA+ transitions remain
unchanged; the malformed-result regression is separate evidence outside their earlier
input assumption.

## Maintainer assessment

The patch is small, directly tied to the documented fail-safe contract, and has a
before/after regression. An upstream reviewer should confirm that superseded is the
intended terminal for malformed output after accepted settlement; publishing an error
instead would be a different audit contract. The benefit is resilience to buggy custom
evaluators. No frequency, field incident, or customer impact has been established.

This is a prepared contribution packet. It has not been sent to upstream maintainers.
