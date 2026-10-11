# Bounded discovery process

Started 2026-10-10 after the [question audit](../evaluation/question-audit.md).
The earlier continuation-testing proposal remains stopped. This is exploratory
problem discovery, not confirmation of another contribution or an exhaustive review.

## 1. Independent evidence

Use three independently implemented engines: Temporal (`temporalio/sdk-python`),
DBOS (`dbos-inc/dbos-transact-py`), and Restate (`restatedev/restate`). This is a
purposive selection for accessible implementation, public issue history, and
different durability architectures; SDK languages do not count as independence.

For each repository, search GitHub issues (excluding PRs), created from 2025-01-01
through 2026-10-09, separately for `cancel`, `replay`, and `version` in title/body.
Retrieve the first five results in ascending creation order per query; deduplicate
by repository/issue number. Preserve query, total match count, selected URLs, dates,
body hashes, and bounded excerpts in a CI artifact. Include open and closed issues.
These keyword/repository/time bounds introduce selection bias: no prevalence or
completeness estimate follows. Empty searches and setup failures remain recorded.
The total initial screen is at most 45 issue-query entries. Read selected primary
reports and relevant official contracts; record exclusions and context.

Earlier inspected Temporal cases and DBOS #358 are development knowledge, not
holdouts. An initial documentation orientation has also covered cancellation APIs;
this does not predetermine the winning question. Search terms privilege lifecycle
and recovery concerns and may miss other important problems.

## 2. Candidate development

Develop at most three questions. For each record a user decision/consequence,
supporting cases from the screen, closest prior answer, potential added knowledge,
and the cheapest observation that could undermine the question. Known bugs can
support an empirical study. A taxonomy alone is not the contribution.

## 3. Exploratory probes

Publish a separate protocol before execution: exact subjects/dependencies,
controls, observations, limits, and possible interpretations. Run executable probes
and validation in GitHub Actions only. Local work is reading, editing, and preserving
CI output. Record every planned arm, failures, and inconclusive setups. Avoid a
generic cross-engine pass/fail oracle when the engines promise different contracts.

## 4. Claim selection

Choose a substantive empirical, theoretical, or methodological claim only if the
exploration supports it. State its scope, nearest precedent, remaining uncertainty,
and a decisive evaluation plan. A negative outcome may reject all candidates.
Exploratory observations do not become held-out validation retrospectively.
Never count repeated executions as independent defects or public issue counts as
production failure rates. No tool advantage is required for every kind of science.

## 5. External challenge

Publish a short review packet and a public review request in this research
repository, with exact evidence and questions that could invalidate the proposal.
The user's instruction to carry out all five steps authorizes that review request.
Do not open speculative bug reports in upstream projects or claim an independent
review has happened before a real response is received. Record any response and
remaining objections; an unanswered invitation leaves this step awaiting feedback.

## Completion and limits

Deliver the screened inventory, up to three assessed candidates, CI results, a
selected or rejected claim with evaluation plan, and an external-review handoff.
An actual independent response cannot be manufactured or guaranteed in this session.
The process seeks a strong contribution; it does not promise one. Update the
discovery status as each stage completes and retain superseded predictions.
