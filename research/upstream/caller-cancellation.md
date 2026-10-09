# Preserve caller cancellation while settling evaluator cleanup

[Measured results](../evaluation/cancellation-results.md) · [Minimal patch](caller-cancellation.patch) · [Standalone regressions](test_cancel_and_settle.py)

## Problem and trigger

`_cancel_and_settle` documents that workflow cancellation must propagate, but catches
`asyncio.CancelledError` without distinguishing the child evaluator from its waiting
caller. An outstanding caller cancellation can therefore be consumed. If approval
already settled, the caller can proceed to tool execution despite being cancelled.

The deterministic trigger is:

1. A custom evaluator starts and waits.
2. Human approval settles the gate; the runner cancels the evaluator and awaits cleanup.
3. A supported custom-agent signal cancels the message-handler task waiting in cleanup.
4. The evaluator either re-raises this second cancellation or suppresses it and returns.
5. The original helper returns normally; the concrete `tool_start` event follows.

The real Temporal reproducer uses public harness APIs and ordinary asyncio task
cancellation. It does not call a private approval handler. The accepted approval stays
approved. A separate public `WorkflowHandle.cancel()` control ends as CANCELED; this
packet does not claim that global workflow cancellation is broken.

## Proposed correction

After settling the child, inspect the caller's outstanding cancellation count and
propagate `CancelledError`. Checking after a normal child return also covers a child
that suppresses the second cancellation. Ordinary child cancellation, cleanup errors,
and returned cleanup results remain discarded.

The superseded-evaluation path closes its terminal record before propagating a live
caller cancellation. Publication is guarded by `workflow.in_workflow()` so offline
workflow eviction does not publish on a destroyed workflow loop. The complete Temporal
experiment checks exactly one terminal and no tool start on the corrected caller path.

The policy treats a nonzero `Task.cancelling()` count as an outstanding request.
Code intentionally consuming a caller cancellation must explicitly clear that request
with `uncancel()`; a regression covers that case. Python 3.11 or newer is required,
consistent with the project. This is a proposed contract for maintainer review.

## Validation and application

The patch is generated against original upstream revision
`049e01c9d726ef68bff7be857c735723b9801512` and contains only the helper correction,
the superseded-path audit correction, and seven standalone asyncio regressions.
It does not depend on the earlier malformed-result patch or the research tooling.

On that clean original source, the seven regressions produced **three assertion
failures and four passes**: both second-cancellation responses and the pending caller
request failed the required propagation contract. After applying the patch, **all seven
passed**. These are helper tests, not a full upstream compatibility matrix.
The [original JUnit record](../evaluation/cancellation-evidence/upstream-original.xml)
and [patched record](../evaluation/cancellation-evidence/upstream-patched.xml) are retained;
the results snapshot checks their hashes and counts.

```bash
git apply --check caller-cancellation.patch
git apply caller-cancellation.patch
uv run --frozen pytest tests/harness/test_cancel_and_settle.py -q
```

Separately, [final study run 37893542636](https://github.com/charifmahmoudi/temporal-agent-harness/actions/runs/37893542636)
passed 23 baseline and 23 isolated-correction tests, sixteen completed-history replays
per variant, six expected TLC results, and all 375 harness regressions against the isolated
correction. Its corrected source also includes the
earlier malformed-result guard; source hashes are retained in the results snapshot.

## Scope and review request

**Rollout caveat established by the [activity-backed study](../evaluation/activity-results.md):**
the direct correction cannot replay the two retained baseline caller histories that
already scheduled an activity. Live nonsticky replacement records explicit workflow-task
nondeterminism. The [versioned study diff](caller-cancellation-versioned.patch) preserves
the tested baseline histories and protects the tested new path; it does not accept every
history produced by the unversioned correction. It targets the research baseline,
is supplied for review, and is not a universal migration recommendation. All 375
existing harness regressions pass against that isolated versioned source.

The subsequent [upgrade experiment](../evaluation/upgrade-results.md) found successful
command replay for all retained histories under both variants, but changed application
outcomes in the two caller-cancellation scenarios in each direction. This is expected
behavioral correction for a workflow-local probe; it is not evidence of external-effect
rollback or a validated live rollout. Review deployment/versioning separately for
activity-backed tools and in-flight workflows. The new experiment passed locally
and in GitHub Actions with identical categorical outcomes and retained evidence.

This is inspection-led discovery with targeted implementation evidence. TLA+ makes
the missing invocation obligation explicit; it did not discover the initial defect.
There is no measured production incidence, external-effect rollback, arbitrary-child
termination guarantee, or universal replay proof. Maintainers should review the
outstanding-request policy and evaluation-terminal behavior, including SDK eviction.

Prepared for review; **not submitted upstream or accepted**. The correction remains
isolated on the research branch to preserve its measured baseline.
