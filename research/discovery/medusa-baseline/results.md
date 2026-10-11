# Medusa return baseline — qualification result

**Qualified for this normal-path case in GitHub CI. No fault/recovery result or
scientific novelty is claimed.**

[Successful run 38073212334](https://github.com/charifmahmoudi/temporal-agent-harness/actions/runs/38073212334)
ran implementation commit `533d5fa18dc18d25797ba11101ef1a5bf77c324f`, with PR merge
checkout `3aa5ee9b69bd91bb670b9ae3ddbecd5f0b7b0cf7`.
Jest reports one passed test and zero failed tests. The job additionally requires a
successful Jest result and the qualification summary. There are no repetitions to
interpret as independent scientific trials.

## What we now have

A runnable Medusa 2.21.2 application fixture using its existing core workflows,
a separate durable payment test process, a PostgreSQL observer connection, and retained
stage snapshots. See the [frozen protocol](protocol.md), [implementation](../../medusa-baseline/),
and [CI workflow](../../../.github/workflows/medusa-baseline.yml).

The fixture begins with a seeded fulfilled/shipped order for two USD25 items.
It captures USD50, requests the two items back, receives one as resellable and
one as damaged, confirms receipt, then issues an explicit USD50 refund.
No application source or recovery safeguards were patched.

| Independent observation | Before return | After receipt | After explicit refund |
| --- | ---: | ---: | ---: |
| Sellable inventory | 0 | 1 | 1 |
| Return received quantity | No return | 2 | 2 |
| Damaged quantity | No return | 1 | 1 |
| Provider capture total (USD) | 50 | 50 | 50 |
| Provider refund count | 0 | 0 | 1 |
| Provider refund total (USD) | 0 | 0 | 50 |
| Latest order pending difference (USD) | 0 | -50 | 0 |
| Latest order refunded total (USD) | 0 | 0 | 50 |

Return status after receipt and refund is `received`. The application has one USD50
capture, one USD50 refund, and corresponding +50/-50 order transactions. Independent
provider SQLite contains one capture and one refund with Medusa-supplied operation keys;
read-only inspection of the retained database agrees with the JSON snapshots.

Receipt and settlement are distinct operations here. This agrees with the inspected
workflow source; it is not a newly discovered inconsistency. After receipt, the application
truthfully records a refund obligation. Explicit refund settlement resolves it.

## Provenance and evidence

- Source inspected: Medusa v2.21.2, commit
  `020565398e436a2bc65777a3b1ad347b4735d6df`, MIT.
- Executed application packages: exact npm 2.21.2 releases. Source checkout and npm
  distributions are separately identified, not assumed byte-identical.
- Node: v22.23.3. PostgreSQL 16.15 observed in the job log; service configured as `postgres:16`.
- [Committed dependency lock](../../medusa-baseline/package-lock.json), SHA256
  `4f33a438909d430be7b82ce44baf26d29d1478a6287c08ebe55fdc9ffcc44831`.
  The successful run uses `npm ci`; retained npm inventory has no reported dependency
  problems. This is not a vulnerability audit.
- [Successful raw artifact](evidence/attempt-7.zip), SHA256
  `2a8ff3b8ea2f1aba8a97de0dc184054d7a723d7cb840a234fd246a7e927199fb`.
  It includes all three committed-state snapshots, request/event logs, provider SQLite,
  Jest result, dependency inventory, lock, checkout identity and runtime version.
- [All-attempt manifest](artifacts.json) records original ZIP hashes and CI links;
  exact downloaded archives are committed so CI artifact expiry does not erase them.
- [Summary](summary.json) is a convenience; raw snapshots and database are authoritative.
  No experiments or application execution ran locally. Local work was source inspection,
  authoring, and reading/preserving CI artifacts.

## Setup failures remain visible

Six earlier attempts failed qualification: Jest VM setup; provider capture interface;
invalid initial lock placement; misuse of the runner database proxy; refund serialization;
and native numeric conversion of a raw Medusa amount. These were harness/dependency/
observer errors, not six Medusa defects. The first job was incorrectly green because
its shell pipeline hid Jest's failure. Explicit bash/pipefail and mandatory result checks
were added. See [attempt log](attempts.md) for each correction and retained evidence.

The latest provider uses Medusa's own BigNumber decoder, retains the raw representation,
and emits a finite numeric amount for this small-integer fixture. Earlier raw observations
were not rewritten to make them pass.

## Limits and next decision

The baseline is now usable for designing a question about this application's operational
decisions. It is not production telemetry, a full storefront/delivery integration,
a real payment provider, a human-effort measurement, or an LLM evaluation. The provider
supports the full-capture case here; general partial-capture, decimal precision, key expiry,
concurrency and reconciliation semantics have not been qualified.

No process crash, timeout, duplicate delivery, restart, or durable workflow-engine recovery
was exercised. Default test-application configuration must not be mistaken for a
production recovery deployment. Images and runner labels are mutable; the application
dependency lock is retained.

Stop at normal-path qualification in this round. Any next fault experiment must first
identify a specific operator decision and a competent existing recovery baseline, inspect
the relevant persistent-engine configuration, and freeze a separate protocol in GitHub.
A failure at a chosen boundary would still require an explanation and nearest-work check;
it would not automatically establish a scientific contribution.
