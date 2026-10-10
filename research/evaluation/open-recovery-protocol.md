# Open-workflow recovery: development protocol

Recorded 2026-10-10 before implementing or executing this experiment. Development
case: Temporal Rust SDK PR [1353](https://github.com/temporalio/sdk-rust/pull/1353).
The report and fix have been read; no cell is an independent holdout.

## Question and controls

Does an additional activation after an asynchronous Nexus result expose a failure
that immediate completion hides? Is reconstruction necessary, or does a cached
execution also fail? The second question matters: the report's description must
not substitute for a causal control.

Use the upstream asynchronous Nexus fixture and its backing workflow. Keep the
operation, outcome, result assertion, server, and worker settings constant except:

| Factor | Levels |
| --- | --- |
| SDK source | affected `0689f769ccc440e8d5008d4a623dee3c82a94ff2`; fixed `d936c6cc6455256417c917c3637d52e53acb8178` |
| Continuation | return the Nexus result immediately; await a one-second SDK timer before returning that same result |
| Cache | default cache; `max_cached_workflows = 0` to reconstruct on subsequent tasks |

Run all eight cells three times, sequentially within each release arm. The timer is
a legal SDK continuation and an activation barrier, not an arbitrary host sleep.
This is a first-stage context test. It does not exercise legacy queries, explicit
eviction, abrupt process loss, or application signals. Default cache is a warm-path
control, not proof that an eviction never occurred; inspect history and logs.

Use Rust 1.94.0 and the upstream lockfile. Pin Temporal CLI 1.7.0 for both arms
(Linux amd64 archive SHA-256
`8b5de72e622f4ae062d0d5d948ca398de6212d63b2f25766a1cb810a3dc2d0ed`).
Record the server's version, archive hash, source revision, generated fixture,
source diff, dependency lockfile, command exit status, logs, and full histories.
Use `cargo integ-test` as required by upstream contributor guidance. Compile before
measuring; permit 20 seconds for each live fixture and 180 seconds per invocation.
This bound is a progress alarm, not a deadlock theorem.

## Scoring

- **Successful cell:** expected logical payload, completed live workflow, no
  recorded workflow-task failures/timeouts, and successful completed-history replay.
- **Confirmed mechanism:** retained failure explicitly contains `TMPRL1100` and
  the non-SDK-wake message. Record live versus offline phase. Do not infer this
  mechanism from a nonzero command status alone.
- **Other semantic discrepancy:** wrong payload or unexpected completed state;
  investigate separately rather than relabel as TMPRL1100.
- **Inconclusive:** compilation/setup failure, absent history, unclassified
  exception, or an alarm without corroborating mechanism evidence.

Cache-off may expose other defects before the relevant result boundary. Require
the retained history to show the operation completion before assigning this case
to the proposed mechanism. Preserve all outcomes; do not discard difficult cells.

## Predictions and decisions

The source report predicts affected/open/reconstructing failure and fixed success.
Immediate completion is expected to pass based on upstream tests. Cached/open is
deliberately unresolved; it tests whether another activation alone is sufficient.
These are source-informed predictions, not prospectively discovered bugs.

If cached/open also fails, narrow the mechanism to activation/observer lifetime;
do not claim that restart is necessary. If completed cells fail identically,
reject the missed-open-context claim for this fixture. If the fixed arm fails,
investigate before attributing an affected-arm failure to the patch. If nothing
reproduces, retain the negative result and do not build a selector around the lead.

Only after this gate should query/restart treatments and a second result-identity
mechanism be added. Selection comparisons must share the same continuations and
oracles. State-identification testing, exhaustive bounded cuts, random cuts,
dependency-based selection, and upstream regressions are required baselines.
