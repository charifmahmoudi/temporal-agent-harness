# Replication and evidence audit: durable-workflow recovery

Date: 2026-10-11  
Status: bounded reproducibility report; no strong novel scientific contribution established.

## Executive finding

This project produced reproducible, CI-run evidence about known workflow-recovery behavior and qualified a public benchmark artifact. Those are concrete outputs. The results support replication, scope clarification, and reuse guidance. They do not establish a new recovery mechanism, a method advantage, a prevalence estimate, or a general safety claim.

## Evidence and outcomes

| Workstream | Evidence | What it supports | Boundary |
|---|---|---|---|
| Cancellation and incompatible replay | [Prospective protocol](discovery/recovery-protocol.md); [18-trial results](discovery/results.md); [CI run 38059968219](https://github.com/charifmahmoudi/temporal-agent-harness/actions/runs/38059968219) | Three executions per arm on Temporal 1.34 and Restate 1.7.13 matched the engines' known cancellation, replay-mismatch, and termination behavior. | One synthetic workflow family, not independent defects. The outcomes fit existing contracts; they do not show exactly-once external effects under crashes or retries. |
| Continuation selection | [Question audit](evaluation/question-audit.md); [closest-work review](evaluation/continuation-prior-work.md) | Across the recorded schedule, Nexus, local-activity identity, and suffix studies, ordinary enumeration detected the known cases. The proposed delay heuristic showed no advantage on the 72-trial pilot. | Cases and test grammars were known during development. Automatic source analysis, scale advantage, and independent holdout performance remain unestablished. |
| DBOS #880 recovery | [Probe protocol](discovery/incidents/probe-protocol.md); [incident results and evidence audit](discovery/incidents/results.md); [probe CI run 38061962520](https://github.com/charifmahmoudi/temporal-agent-harness/actions/runs/38061962520); [audit run 38062212830](https://github.com/charifmahmoudi/temporal-agent-harness/actions/runs/38062212830) | In eight corrected cells, deleting the conflicting schedule before recovery led both SQLite and PostgreSQL to recreate it. A same-name marker returned the prior value; a different-name marker errored after recreation. Evidence checks preserved all eight initial observer failures as inconclusive and rejected contradictory controls. | A bounded cross-backend replication of the known report and its success-only checkpoint explanation. It does not establish a new mechanism or validate a general fix. |
| UndoBench artifact qualification | [Protocol and results](discovery/baseline-qualification/results.md); [qualification CI run 38066672086](https://github.com/charifmahmoudi/temporal-agent-harness/actions/runs/38066672086); [schema check 38066836075](https://github.com/charifmahmoudi/temporal-agent-harness/actions/runs/38066836075) | Independent recomputation of 2,880 paired records found 1,444 duplicate and 284 missing-effect records. A legacy general CLI path reported zero because expected nested count fields were absent; a strict adapter recovered the counts without changing the recovery aggregate. | The paper itself discloses an initial zero-effect aggregation and reconstruction from wire logs. This is a bounded artifact-reuse warning, not benchmark invalidation or a contradiction of the headline result. |
| Public incident and TTL screen | [14-case review](discovery/incidents/review.md); [selection manifest](discovery/incidents/sources.json); [TTL evidence gate](discovery/incidents/results.md#finite-provider-key-evidence-gate-2026-10-10) | The selected reports identify useful operator decisions and several adjacent duplicate/recovery behaviors. | The sample is purposive and adaptive, includes an overlapping pair, and is not a prevalence estimate. No case identifies a named external write API, documented finite key-retention bound, and workflow replay horizon that can exceed it. |

## Interpretation

The clearest contribution of the current work is a retained, auditable reproduction package and a set of precise scope corrections. The 18-trial probe confirms known contracts. The DBOS probe extends a known report to a second backend. The benchmark check identifies a schema hazard in one reuse path, while the source paper already documents its metric reconstruction. The incident screen did not supply motivation for the proposed provider-TTL study.

Closest-work comparisons further narrow the claims: state-identification and crash-testing work address broad continuation-testing claims; *Resume Means Resume* studies process crash/replay with a separate effect ledger; UndoBench and *Where Does Exactly-Once Live?* study agent recovery under tool/service contracts; recent formal dual-write work analyzes sink evidence and bounded deduplication lifetime. The comparisons are focused, not a systematic review. Details and citations are in the linked assessments above.

## Limits and decision

No production workload, representative incident population, independently selected holdout set, or new recovery method was established. Some issue fixes and reporter logs were not independently executed; the case files record the inspection scope. CI success verifies the declared checks at a revision. It does not establish novelty or external validity.

**Decision:** retain this as a replication and evidence-audit record. Do not claim a strong new scientific contribution or run another experiment on the current proposal. Reopen only with an independently motivated case, an exact unanswered operator decision, the closest-work limitation, and evidence suitable for the scope of the claim. Any future experiment must have a frozen protocol and run in GitHub CI.

All reported experiments were executed in GitHub Actions. No experiment was run to write this summary.
