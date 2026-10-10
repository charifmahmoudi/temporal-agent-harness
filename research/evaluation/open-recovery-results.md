# Nexus continuation: measured context difference

## Finding

The [frozen matched experiment](open-recovery-protocol.md) produced 24 usable
executions. On the affected Rust SDK, returning the successful Nexus result
immediately passes; awaiting one SDK timer afterward fails. Default-cache and
cache-disabled treatments agree. The fixed SDK passes every cell.

| SDK | Immediate / cached | Immediate / cold | Timer / cached | Timer / cold |
|---|---|---|---|---|
| Affected `0689f769` | 3 passed | 3 passed | 3 confirmed failures | 3 confirmed failures |
| Fixed `d936c6cc` | 3 passed | 3 passed | 3 passed | 3 passed |

No cell is inconclusive. These are repetitions of one known development defect,
not six independent defects or validation of a proposed method.

The first affected cached failure follows the timer firing. It is a live
workflow-task failure, before the runner ever invokes offline replay. Thus the
reproducer establishes a **continuation-sensitive activation defect**; explicit
restart is not required by the fixture. The cache setting alone cannot prove
the worker never evicted. Activation instrumentation in the
[follow-up protocol](continuation-protocol.md) will distinguish that remaining
ambiguity. The upstream report's broader query/restart account remains a lead,
not something this experiment has measured.

## Evidence and reproduction

Measured [CI run 38037723644](https://github.com/charifmahmoudi/temporal-agent-harness/actions/runs/38037723644),
driver `37aeb06d9dff65daa7af8b4044a1fe7d5b4d5874`. The
[evidence bundle](open-recovery-evidence.json) contains the original affected and
fixed artifact ZIP bytes with SHA-256 hashes, preserving complete histories,
logs, generated fixtures/diffs, provenance, lockfiles, and server descriptions.
The [derived summary](open-recovery-summary.json) is reproducible with:

```bash
python research/scripts/audit_nexus_evidence.py --check
```

The audit verifies all 24 history hashes, unique case/repetition identities,
actual logical Nexus and workflow result payloads, individual recorded failure
messages after Nexus completion, live/offline phase markers, the shared dependency
lock, identical generated fixture, and server version 1.31.0. It rederives verdicts
from raw data instead of trusting a successful CI job. The experiment workflow
intentionally retains expected fixture failures and can itself conclude success.

CLI 1.7.0 archive checksum and both SDK revisions were pinned. A shared lockfile
was resolved once before both builds; it is retained rather than described as the
upstream lockfile. The affected/fixed diff changes only Nexus result polling and
its import, plus changelog. No byte-identical build or general platform invariance
is claimed. See the original protocol/workflow for live reproduction commands.

## Source explanation and uncertainty

At the affected source revision:

1. `StartedNexusOperation::result` awaits a cloned `Shared` result future without
   the SDK poll guard (`crates/workflow/src/workflow_context.rs`).
2. `PerPollWakeTracker::wake_by_ref` sets a persistent flag when a wake happens
   outside `SdkWakeGuard` (`crates/sdk/src/workflow_executor.rs`).
3. `WorkflowFuture::poll` consumes that flag before processing the next non-eviction
   activation (`crates/sdk/src/workflow_future.rs`). This check does not require
   `activation.is_replaying`.
4. The fixed implementation polls that shared future inside `SdkGuardedFuture`.

This source path explains why a later activation is a relevant observation point
and why immediate termination can mask the flag. It is a source-supported causal
interpretation, not a complete proof of Rust future execution. We have not directly
instrumented every internal wake, isolated a minimal executable SDK state machine,
or established that every legal continuation triggers it.

## Research decision

Gate 1 succeeds narrowly: an ordinary completed-workflow regression shape misses
a real defect exposed by a legal continuation. Recovery is not yet demonstrated
as a necessary condition. The next gate is the conventional suffix sweep and
activation diagnosis, not a novel selector.

The [prior-work comparison](continuation-prior-work.md) rules out claiming that
state-distinguishing continuations or post-recovery operations are new ideas.
No method advantage, automatically inferred grammar, coverage theorem, blind
holdout, independent reproduction, or scientific novelty is established.
