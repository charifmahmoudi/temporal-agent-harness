# Incident round: progress and evidence ledger

Read the [14-case review](review.md), [selection manifest](sources.json),
[discovery protocol](protocol.md), and [frozen probe](probe-protocol.md).

Activities 1–2: report/discussion review and operator-decision extraction complete.
Implementation inspection is scoped explicitly per case, not claimed for every fix.
Activity 3: one eight-cell cross-backend probe selected; collection correction underway.
Activity 4: expansion not authorized by evidence yet; no new method or paper claim.

## Failed initial collection

[Run 38061711702](https://github.com/charifmahmoudi/temporal-agent-harness/actions/runs/38061711702)
on f6a0df71 ran four cells per backend. All first processes reached the declared crash;
all recovery processes failed in the observer before recovery launch because it used
`dataclasses.asdict` on DBOS's ordinary `WorkflowStatus` object. These eight attempts
are inconclusive setup/measurement failures, not engine recovery failures. The fix
uses the object's attributes. Protocol, workload, and predictions are unchanged.

| Artifact | ID | SHA-256 |
| --- | --- | --- |
| SQLite initial | 11673621188 | 6b40edb387fd68d56770984d97e1e79e4e4e537cead24beac30be5de26c4db18 |
| PostgreSQL initial | 11673895775 | 166a17d33b74234cd91f7474a7077fcbd0ad318d4a5374bd74b0948144defd63 |

Raw logs and checkpoint databases remain in these CI artifacts. Retain this failed
attempt separately from subsequent successful collection; do not reduce the denominator.

## Scientific gate

The current review does not establish a new recovery theory or method advantage.
The selected probe can answer an explicitly untested backend scope in a known report.
If it confirms the shared checkpoint explanation, stop at a community reproduction
and scope extension. A success result alone cannot establish preserved effects.
No broader generator, diagnosis framework, or practitioner-performance study is started.

## Source and search limits

[Nearest prior answers](prior-answers.md) records the relevant contracts and overlap.
The study is purposive and adaptive: fourteen issue records include one overlapping
Restate pair and two late DBOS additions. It estimates neither prevalence nor the
number of independent failure mechanisms. Reporter logs and historical fixes were
not all independently executed; the case notes state which implementation changes
were inspected. Only the selected DBOS probe is newly executed in this round.

## Corrected collection and decision

[Run 38061962520](https://github.com/charifmahmoudi/temporal-agent-harness/actions/runs/38061962520)
on dffd27c6890c9f30fe9761bbfcd4eeed15b7e699 completed all eight cells and documentation
checks. The original eight inconclusive attempts remain above. The corrected run had
no collection failures or bounded recovery timeouts. Each row below represents one
execution per backend, not a frequency estimate.

| Operator action | Branch-B marker | SQLite outcome | PostgreSQL outcome | Schedule effect |
| --- | --- | --- | --- | --- |
| Retain | Same name | SUCCESS, A, branch A | SUCCESS, A, branch A | Original schedule remains |
| Retain | Different name | SUCCESS, A, branch A | SUCCESS, A, branch A | Original schedule remains |
| Delete | Same name | SUCCESS, A, branch B | SUCCESS, A, branch B | Schedule re-created with a new ID |
| Delete | Different name | ERROR, unexpected step, branch B | ERROR, unexpected step, branch B | Schedule re-created before terminal error |

Pre-recovery snapshots contain the completed marker at slot 2 but no schedule-operation
row at slot 1. In deletion cells, post-recovery rows add a successful createSchedule at
slot 1 while preserving the old slot-2 output. The branch trace records B, and the
schedule has a new ID. This supports the shared success-only checkpoint explanation;
it rejects SQLite-specific necessity **for this exact workload/configuration**.
It does not prove that all backend behavior is equivalent or validate a proposed fix.

This is a replication and backend scope extension of the upstream report. Its author
and follow-up commenter already supplied the central observation and mechanism.
No new scientific mechanism, method advantage, or broad operator-safety rule follows.
The practical lesson for this fixture is that terminal SUCCESS and the old return
value do not demonstrate that recovery preserved the prior effect state. The effect
here is an engine-managed schedule, not an independently operated payment API.

**Activity 4 decision: do not expand to a new framework or confirmatory study.** All
predicted cells fit the existing source explanation. Reopening requires a specific
unexplained observation or capability gap, a nearest-work comparison, a frozen claim
and evaluation, and independent cases appropriate to that claim. We have not acquired
that evidence. This does not prohibit future exploration on a different question.

## Durable evidence and audit

[Artifact manifest](artifacts.json) supplies hashes, run IDs and artifact IDs for all
four exact ZIPs, retained as base64 in [evidence/initial-sqlite.zip.b64](evidence/initial-sqlite.zip.b64),
[evidence/initial-postgres.zip.b64](evidence/initial-postgres.zip.b64),
[evidence/corrected-sqlite.zip.b64](evidence/corrected-sqlite.zip.b64), and
[evidence/corrected-postgres.zip.b64](evidence/corrected-postgres.zip.b64).
Dependency freezes, process logs, branch traces, raw checkpoint rows, status snapshots,
and schedule IDs are retained. SQLite archives additionally retain the database files.
The PostgreSQL image digest is recorded; its major-version tag is not an immutable
future dependency. The Python wheel version is pinned; no byte-equivalence claim to
the inspected Git tag is made. No runtime probe was executed locally.

The separate [CI auditor](../../scripts/audit_incident_probe.py) verifies ZIP hashes,
all declared cells, starting PENDING state, crash/branch evidence, unchanged marker
records, intervention snapshots, and terminal results. Three deliberately contradictory
evidence variants must be rejected. Its first CI execution is pending; manual inspection
and successful collection are not substitutes for that audit.
