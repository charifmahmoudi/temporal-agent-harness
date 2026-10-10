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
