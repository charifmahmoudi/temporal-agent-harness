# Failed-operation recovery: prospective cross-backend probe

This follows [DBOS #880](https://github.com/dbos-inc/dbos-transact-py/issues/880)
and its discussion, which already demonstrates SQLite branch/output aliasing and a
savepoint caveat. Those findings belong to the reporters. PostgreSQL was explicitly
untested there. The selected question is whether the observed branch/effect divergence
is SQLite-specific or occurs through the shared success-only checkpoint path.

## Alternatives and observations

H1: the failure depends on SQLite transaction behavior; PostgreSQL preserves the failed
operation's answer or otherwise prevents the changed schedule effect.
H2: the shared success-only operation checkpoint is sufficient; deleting the conflicting
schedule between crash and recovery permits recreation on both backends, before any
later step-name mismatch is detected. Source inspection favors H2; H1 is a diagnostic
alternative, not an equally plausible scientific theory.

Freeze DBOS 3.2.0, source commit d324156616281d7d4923bc60851617bdbb70ea5e,
Python 3.12, SQLAlchemy 2.0.54, psycopg 3.2.10, PostgreSQL 16. SQLite version and all
resolved dependencies will be recorded. This is not an affected/fixed comparison.
No production bug frequency or backend-wide theorem will follow.

Eight cells: SQLite/PostgreSQL × retain/delete conflicting schedule × same/different
name of the branch-B marker step. One controlled execution each; no rate estimate.
Fresh database/workflow per cell. First process creates a schedule, runs a workflow
whose create fails with already-exists, records mark(A), then exits abruptly with a
declared exit code. A fresh process optionally deletes the schedule before launch,
then automatically recovers the same pending workflow under the same application
version/executor identity. Schedule timing is held far outside the experiment.

Retain pre/post operation rows, status, schedule state/identity, branch trace, process
exit codes, logs and dependencies. Read state outside the workflow so observation does
not allocate workflow checkpoints. Require branch A and a PENDING workflow with a
completed marker checkpoint before interpreting recovery. Bound recovery at 60 seconds;
timeout/setup errors are inconclusive, not preserved safety.

Predictions: retain controls return A without schedule recreation. Delete/same-name
cells may return recorded A despite executing branch B and recreating the schedule.
Delete/different-name cells may fail on marker mismatch after recreation. Record
contradictions rather than coercing them into pass/fail expectations.

## Decision and expansion

If both backends exhibit H2, publish a narrowly scoped replication/extension of a known
report; do not start an analyzer or claim a new mechanism. If they differ, inspect
checkpoint/transaction evidence before attributing causality to the backend.
Only a substantive unexplained residual or demonstrated tool limitation could justify
a separately frozen evaluation on independent cases. Successful recovery is not proof
that required effects were preserved. This probe checks engine-managed schedule state,
not payment systems or arbitrary external services.

Run all executions and evidence checks in GitHub CI. Publish the protocol before code.
