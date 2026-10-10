# Baseline qualification: findings and next-question assessment

Date: 2026-10-10. [Protocol](protocol.md) published at cfadc98 before execution.
No outreach was performed. No live model inference or local experiments were run.

## What the first CI run establishes

[Qualification run 38066672086](https://github.com/charifmahmoudi/temporal-agent-harness/actions/runs/38066672086)
passed on branch commit 2517e78; actual merge checkout and pinned upstream revision
are recorded in [summary.json](summary.json). The smoke command, both published
metric commands, six upstream freeze-integrity tests, and two independent arithmetic
fixtures completed. Documentation checks resolved 401 relative links.

Passing process exit codes do not imply metric agreement. Inspecting all retained
outputs uncovered the discrepancy below.

| Observation on the same 2,880 paired records | Official general CLI | Dedicated reproduction script | Independent aggregation |
| --- | --- | --- | --- |
| Successful controls | 2,406 | 2,406 | 2,406 |
| Successful recoveries | 1,124 | 1,124 | 1,124 |
| Conditional recovery | 46.72% | 46.72% | 1,124 / 2,406 |
| Duplicate incidence | **0.00%** | 50.14% | 1,444 / 2,880 |
| Missing-effect incidence | **0.00%** | 9.86% | 284 / 2,880 |

There are no repeated pair IDs and no fault successes outside successful controls.
Each method has 960 pairs and 802 successful controls. Recovery counts are
343 (B0), 429 (B2), and 352 (B5). Unsafe-retry labels agree with duplicate flags
on every row. These are recomputations of the authors' retained results, not
2,880 new executions or independent validation of the original semantic oracles.

## Located discrepancy

At pinned upstream commit
[4a25c4f](https://github.com/tradertanmay/undobench/tree/4a25c4fa0f12bb6c79dc6e0e3a8f31deeb6af21e),
[recoverbench/engine.py](https://github.com/tradertanmay/undobench/blob/4a25c4fa0f12bb6c79dc6e0e3a8f31deeb6af21e/recoverbench/engine.py)
passes the legacy nested oracle verdict to the evaluator, which reads
duplicate_effects_count and missing_effects_count with zero defaults. The legacy
pair verdict instead retains duplicate_effects and missing_effects. The first
duplicate example, pair_RB-CRM-004_M1_F1_B0_t0_7f3028, has duplicate_effects=1
and boolean oracle properties but no nested count fields. This is not a zero-effect
observation; it is absent telemetry being interpreted as zero by this entry point.

The upstream reproduction guide also displays unsafe retry 60.97% and missing
effects 10.83%, whereas the dedicated script yields 50.14% and 9.86%.
The stored committed_mutations scalar differs from the effect-log count in 2,862
records. The dedicated script already reconstructs from effect logs; therefore
this scalar discrepancy is a reuse warning, not a refutation of its results.
The paper acknowledges retrospective effect reconstruction.

A [separate frozen schema protocol](schema-protocol.md) tests the cause by adding
only the two missing nested counts in a temporary copy, rejecting conflicting
fields and absent source counts. Upstream code and original data are unchanged.

[Schema run 38066836075](https://github.com/charifmahmoudi/temporal-agent-harness/actions/runs/38066836075)
passed on branch commit 6db78ae. All 2,880 rows lacked both nested count fields.
The strict adapter restored 1,444 duplicate and 284 missing trials; control,
recovery and EOR counts remained unchanged. Both malformed-input controls were
rejected. [Exact schema output](schema-audit.json) and [retained schema ZIP](schema.zip.b64)
are included. Artifact 11675194519 has SHA-256
4131642af318ebc648285816f8cddc260f83c95bc45b94563bc42aee758761a9.
This verifies the narrow cause and workaround; it does not change upstream files.

## Research decision

The frozen primary dataset is usable for the reproduced aggregate comparison.
The advertised general evaluator is unsafe for interpreting legacy effect counts
without explicit schema adaptation. Use the dedicated script plus independent
aggregation, or the tested strict adapter, for this dataset. Do not treat a green
smoke check as evidence that all reporting entry points agree.

This is a concrete artifact-reuse finding. It is not yet a strong scientific
contribution, a newly established agent failure mechanism, or evidence that the
paper's main competence/recovery result is false.

| Candidate | Decision and reason |
| --- | --- |
| Show that ordinary completion hides recovery failures | Already studied by UndoBench; reject as a new claim |
| Add real process crashes and a separate effect ledger | Resume Means Resume already does both; reject the generic novelty claim |
| Study safe continuation of composite operations under constrained inspection and repair APIs | Retain as a question, not an established gap; requires a precise baseline and independent workload mapping |
| Claim the metric discrepancy establishes a general benchmark failure pattern | Reject: one pinned artifact/entry point cannot establish prevalence or generality |

Further reading of Resume Means Resume covered its contract, external-effect
composition, engine comparison and validity discussion (sections III, VIII–IX).
It explicitly separates caller-provided effect idempotency from persistence-plane
guarantees. Merely combining a durable engine with a tool does not establish a
new method.

A concrete next study would need to vary service repair capabilities while holding
the workflow and durable engine fixed, compare idempotency, transaction and
compensation baselines, and measure safe completion separately from safe abstention.
A real checkpoint boundary and restart-surviving service state are required.
Before implementation, compare the proposed claim with existing durable-functions,
resumable-operation and crash-consistency methods. No method-superiority study
is justified yet.

A further reuse limit comes from source inspection: the standard ToolProxy's
DURING_MUTATION hook raises before calling the tool, and the upstream qualification
test expects unchanged state. That entry point alone cannot reproduce a partial
composite mutation. The paper's secondary partial-mutation results must be mapped
to their actual specialized execution path before reuse; we have not reproduced
those runs and do not infer they are invalid.

## Retained evidence

[qualification.zip.b64](qualification.zip.b64) retains the exact CI artifact ZIP
11674874466, SHA-256
2af0e73167135c0b91586a2519c70a3566d26369aa8d8db5b27f582ce6e38ad6.
It contains command logs, dependency resolution, runtime and summary. Decode base64
to recover the ZIP. The upstream primary dataset is pinned by commit and the
published hash in the protocol; it is not copied into this repository.
The full comparison must retain both zero-valued CLI output and nonzero script
output. Neither is discarded as an inconvenient run.
