# Public-evidence continuation: baseline qualification

Date: 2026-10-10. Status: protocol published before execution.

## Scope and communication

Continue using public papers, source and GitHub CI. No person-directed comments,
mentions, email, or upstream reports are authorized by this round. Any future
outreach requires the user's explicit approval of both recipient and message.
This supersedes the external-challenge action in the earlier discovery protocol.
Historical results and invitations remain historical records.

## Question and rationale

Can an existing recovery benchmark supply an independently authored workload and
auditable baseline for studying the boundary between external acknowledgement and
durable checkpoint? Before extending it, establish that the retained data and
advertised reproduction entry points support the baseline claims.

This is artifact qualification, not a new scientific contribution or a replication
of live model inference. A missing benchmark boundary alone does not establish
novelty: durable execution and crash-consistency work already study this problem.

## Focused prior-work screen

Searches: durable agent workflows recovery benchmark external effects time travel
fork approval research paper; durable execution workflow compensation recovery
research; exact-title verification with a second search engine. Purposive search,
not systematic coverage or proof of absence.

| Source | Inspected scope | Consequence |
| --- | --- | --- |
| [UndoBench v1](https://arxiv.org/html/2610.05622v1), Sah et al. | Sections 2–7, limitations; artifact README, reproduction guide and metric script | Already studies paired task competence/recovery, effect histories and mutation timing. Acknowledgement-to-checkpoint crashes are explicitly outside its synchronous harness. |
| [Resume Means Resume v1](https://arxiv.org/html/2608.03836v1), Khan | Abstract and introduction | Already reports model-free crash/resume conformance across frameworks. Abstract-level overlap rules out claiming generic crash/resume testing as new; detailed comparison remains required. |
| [Stop Means Stop](https://arxiv.org/abs/2607.14166), Khan | Abstract | Already studies approval, cancellation and timeout enforcement. Do not relabel those distinctions as a new contribution. |
| [Pilot Execution](https://www.usenix.org/conference/nsdi26/presentation/li-zhenyu), Li et al. | Official conference abstract only | Recovery dry-runs and cross-component failures already have a published method; full-paper comparison required before any overlapping proposal. |

These are attributed author claims, not independently verified findings here.
Preprints are not treated as peer-reviewed merely because an artifact exists.

## Frozen subject and observations

[UndoBench source](https://github.com/tradertanmay/undobench/tree/4a25c4fa0f12bb6c79dc6e0e3a8f31deeb6af21e)
at 4a25c4fa0f12bb6c79dc6e0e3a8f31deeb6af21e. Dataset:
results/rb3c_test_raw.jsonl, published SHA-256
1016768449aae019484130b23fda33456861abeb161a5f8dfbeb16e9e5e9f882.

Run only in GitHub Actions, Python 3.12:
1. Published smoke command; save output and exit code.
2. Published offline evaluate command and reproduce_eor.py; retain both outputs.
3. Upstream freeze-integrity tests.
4. Independent standard-library aggregation of the frozen paired records.

Record pair count, unique IDs, method counts, control successes, fault successes
both conditional and unconditional, duplicate/missing flags, UNSAFE_RETRY labels,
and whether any fault success occurs without control success. Compare flagged
committed counts with raw effect-log counts, without treating either as a new
semantic oracle. Record disagreements rather than silently selecting one source.
Require hash agreement before interpreting aggregate results.

Predictions from the paper: 2,880 pairs, 2,406 successful controls, 1,124 successful
recoveries; per-method controls 802/960. The guide's unsafe-retry example appears
different from the paper's equality of unsafe retry and duplicate incidence.
This is an inspection lead, not a declared measured defect. Zero discrepancies
would reject that lead; discrepancies trigger row-level inspection before any
research claim. An execution/setup failure is inconclusive.

The independent aggregator has small contrasting fixtures: a fault success with
a failed control must not enter a conditional numerator; duplicate-only and
missing-only rows must remain distinct. These validate arithmetic, not scientific
novelty. All command failures remain in the record; no model calls or API keys.

## Decision gate

If qualification succeeds, assess one candidate: whether checkpoint placement and
the external service's recovery interface change safe continuation on independently
authored composite workloads. First compare with Resume Means Resume, durable
functions semantics and crash-consistency testing in full. Existing idempotency,
transactions and compensations must be baselines, not omitted competitors.

Do not start a framework or large model campaign on this evidence. If qualification
fails, document exactly what failed and whether it blocks reuse. Artifact defects
alone do not establish a strong research contribution. No author contact follows.
