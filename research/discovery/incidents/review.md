# Consequence-led incident review

Fourteen report/discussion records across three engines; purposive discovery, **not
fourteen independent defects or a representative sample**. The [source manifest](sources.json)
records selection and comment permalinks. Earlier inspected Restate cases remain
contaminated development knowledge. Added DBOS #837 and #880 adaptively after the
initial twelve cases; neither is a holdout. Full discussion reads are distinguished
below from direct implementation inspection. Linked log archives were not independently
reprocessed, and production consequences remain attributed to the reports.

## Operator decisions and closest existing answers

### Temporal server #6514: database reconnection loop

[Report and discussion](https://github.com/temporalio/temporal/issues/6514).
Operators reported stalled workflows after upgrading to 1.25.0, with restart of
server, database, and workers ineffective; rollback to 1.24.2 restored service.
The decision was whether to restart, downgrade, or repair connectivity. Maintainers
requested the underlying connection errors rather than treating a throttled-refresh
message as the root cause. The reporter subsequently confirmed stability after a
patch release. We inspected [PR5926](https://github.com/temporalio/temporal/pull/5926),
which introduced reconnection handling; it is **not** the corrective patch. Exact
fix attribution remains unverified here. No external-effect ledger is supplied.
Disposition: consequential known regression with reported resolution, not evidence
that the mechanism is unexplained. A safe general rollback rule cannot be inferred.

### Temporal server #3826: cluster startup after upgrade

[Report and discussion](https://github.com/temporalio/temporal/issues/3826).
Workflow creation stalled around 1.19.0/1.19.1. Operators tried waiting, downgrade,
and clearing membership state. A 20-second delay helped one reporter but not another;
retain that contradiction. Direct inspection of
[PR3911](https://github.com/temporalio/temporal/pull/3911) shows the start timeout
becoming the maximum of its old value and twice membership join duration. A reporter
then tried twenty rapid restarts successfully. Decision: which recovery action
addresses startup/membership rather than workflow code? Existing fix explains this
case. Listing workflows after restart is weaker than an external-effect safety check.
Do not turn the reported table deletion into a recommended generic recovery procedure.

### Temporal server #1829: cron workflows cease progressing

[Report and discussion](https://github.com/temporalio/temporal/issues/1829).
The apparent missing task writes were later corrected: the deployment separated
reads and writes, so a successful write was not immediately visible on the read path.
An initial suggested upgrade did not fix it. Maintainers asked for timestamped history
and task-queue pollers; the reporter eventually identified the database routing issue.
Decision: repair workflow scheduling, upgrade, or correct storage consistency?
Resolution supports the latter for this report. No independent database trace or code
patch was inspected; this is a reporter-confirmed configuration explanation. Exclude
it from a count of engine data-loss defects. Stale reads and read-your-writes are
established concepts, not a new durable-workflow mechanism.

### Temporal server #2464: repeated archival after an ambiguous response

[Report and discussion](https://github.com/temporalio/temporal/issues/2464).
An archival request timed out from the sender's perspective while the receiver still
archived and removed the live history. Retrying then found no history. The operator
explicitly worried that suppressing an error could lose irreplaceable history.
The maintainer explained that the change affected missing-history error handling,
not signaling retries, which continued until delivery. Decision: does the proposed
mitigation weaken archival durability? The discussion answers its intended scope;
the referenced patch was not identified independently here, so its implementation
and end-to-end no-loss property remain unaudited. This is not observed data loss or
new evidence for the familiar ambiguous-RPC-outcome problem.

### DBOS Python #544: concurrent requests with one workflow ID

[Report and discussion](https://github.com/dbos-inc/dbos-transact-py/issues/544).
A document-processing user expected concurrent content-keyed calls to avoid duplicate
processing; the workflow body ran multiple times. Maintainers distinguished direct
execution from queue admission and pointed to documented step-level behavior. The
reporter confirmed queues met the immediate need. Decision: is a workflow ID alone
sufficient admission control? Existing guidance and a confirmed workaround answer
this case. The example had no steps; it does not establish duplicated committed
transactional effects. The linked TypeScript change was not treated as proof of a
Python fix. No new experiment selected.

### DBOS Python #714: concurrent patch calls and unbounded waiting

[Report and discussion](https://github.com/dbos-inc/dbos-transact-py/issues/714).
The report describes checkpoint-position conflicts being mistaken for another live
execution, leading to polling with no producer. The operator needs to distinguish
legitimate duplicate ownership from unsafe intra-workflow concurrency. The discussion
explicitly rejects interpreting the reporter's race-avoidance algorithm as sufficient
for deterministic replay. Direct inspection of merged
[PR715](https://github.com/dbos-inc/dbos-transact-py/pull/715) confirms a probe,
revalidation, synchronous reservation, and explicit `DBOSPatchNondeterminismError`;
its regression expects ERROR rather than a hang. This is detection of unsupported
interleaving, not a new general concurrency guarantee. Prior report rates are not
our measurements. A terminal error also says nothing by itself about prior effects.

### DBOS Python #770: stream duplicates inside retrying steps

[Report and discussion](https://github.com/dbos-inc/dbos-transact-py/issues/770).
A stream consumer sees each retry's output although the containing workflow succeeds.
Decision: can an operator retry the step without duplicate stream entries? Maintainers
state that steps are at-least-once. Current
[Python communication documentation](https://docs.dbos.dev/python/tutorials/workflow-communication)
also distinguishes stream writes from workflows and steps. The reported source paths
explain this context dependence; no affected/fixed comparison is warranted for intended
behavior. This is a useful contract clarification, not an unexplained safety failure.
Current documentation does not prove what documentation said when the issue was filed.

### DBOS Python #702: debouncer stuck across application versions

[Report and discussion](https://github.com/dbos-inc/dbos-transact-py/issues/702).
A new deployment sends to a deduplicated debouncer owned by old code that is no longer
running. Version-prefixed keys avoid collision but do not establish safe completion
of old work. The operator's real choice is version routing/draining versus compatible
patching. The maintainer points to
[upgrade guidance](https://docs.dbos.dev/python/tutorials/upgrading-workflows), and the
reporter accepts static version plus patching as the path forward. No independent
runtime validation here. This is a resolved usage question with an explicit operational
consequence; changing a key namespace is not automatically a safe migration.

### Restate #2565 and #2655: availability after network healing

[#2565](https://github.com/restatedev/restate/issues/2565) and
[#2655](https://github.com/restatedev/restate/issues/2655) are related Jepsen campaign
reports, grouped to avoid inflating independence. Requests timed out after healing;
restarting processes or a particular leader restored progress in reported runs.
One run recovered spontaneously after about four minutes. Several attempted fixes
failed retesting; eventual resolution followed a batch of changes. We inspected
[PR2570](https://github.com/restatedev/restate/pull/2570),
[PR2673](https://github.com/restatedev/restate/pull/2673), and
[PR2683](https://github.com/restatedev/restate/pull/2683). They cover controller/log
handling, sequencer cancellation/drain, and interval handling respectively. None is
claimed to be the sole proven cure; the discussion contradicts that simple attribution.
Decision: wait, restart a follower, or restart a leader, and on what evidence?
The public record supplies case-specific observations, not a universal safe decision
rule. Ordinary Jepsen testing already exposed these failures. Repeating it is not a
new testing contribution, and our review did not independently inspect its full
consistency histories.

### Restate #4838: upgrade, cleanup, snapshot restore, disk exhaustion

[Report and discussion](https://github.com/restatedev/restate/issues/4838).
A node crash-looped after 1.6.2 to 1.7.0-rc.1; snapshot staging then filled its disk.
The cluster continued serving on other nodes, so this is degraded redundancy, not a
reported total outage. Recovery reportedly required wiping the local partition store
while retaining log and metadata stores. The first hypothesis (only this node had
orphans) was corrected: all nodes had orphans; only the failing node overlapped cleanup
with fast-forward restore. The discussion traces a background write racing a dropped
column family and a shared RocksDB failure. A maintainer endorses lifecycle management
so no writes outlive the partition processor. We read that source analysis, but did
not independently rebuild its archived revision or identify a final corrective commit.
Decision: which state can be discarded and reconstructed without losing obligations?
This is consequential, but a safe wipe requires snapshot/log coverage evidence absent
from a generic health status. Resource lifetime and recovery atomicity already explain
the described mechanism; no new theory established. Do not publish the wipe as advice.

### Restate #4513: completed workflow appears missing

[Report](https://github.com/restatedev/restate/issues/4513); no discussion returned.
The report traces `/output` returning 404 from a follower before it has replayed a
completed invocation, while `/attach` follows a stronger path. Decision: retry a
read, resubmit work, or declare history lost? The report's proposed leadership guard
fits established consistency reasoning. Code paths and CI reference are supplied by
the reporter; we have not independently replayed its trace or verified a merged fix.
A 404 is not sufficient evidence of lost execution. Keep this as a source-supported
lead, not a measured current defect or validated recovery recommendation.

### DBOS Python #837: durable function-name collisions

[Report and discussion](https://github.com/dbos-inc/dbos-transact-py/issues/837).
The initial report tested registration only and inferred wrong-function recovery.
Later discussion references another person's full recovery measurement, a merged guard,
and a remaining same-module case intentionally left as a warning. Decision: is the
registration warning harmless re-importing or a conflicting recovery target? Current
3.2.0 registry source was inspected, but the historical full recovery artifact was
not obtained. The origin-path heuristic and its limits are already discussed upstream.
Do not label the initial inference our discovery or claim that closure eliminates all
collisions. No independent validation or novel identity theorem follows.

### DBOS Python #880: forgotten failures change recovery effects

[Report and discussion](https://github.com/dbos-inc/dbos-transact-py/issues/880).
An internal schedule operation records success but not failure. After a crash and an
operator's deletion of the conflicting schedule, replay can create it and follow a
different branch. The discussion already measures SQLite: a same-name marker returns
old output; a different-name marker errors after the new schedule effect commits.
It also tests a proposed repair and warns about SQLite savepoint behavior. PostgreSQL
was explicitly untested. We inspected `call_txn_as_step`, `create_schedule`, registry
handling, and recovery launch in source commit
[d324156](https://github.com/dbos-inc/dbos-transact-py/tree/d324156616281d7d4923bc60851617bdbb70ea5e).
The shared success-only path motivates the [frozen cross-backend probe](probe-protocol.md).
Decision: can changing administrative state before recovery cause a new effect despite
an old-looking workflow result? This is a consequential known report. The selected
experiment tests its backend scope, not a new explanation invented here.

## Synthesis before new outcomes

The shortlist is not a new taxonomy. Three candidate decisions emerged:

| Candidate | Closest adequate answer / limitation | Decision this round |
| --- | --- | --- |
| Pick a restart/rollback action from health symptoms | Existing incident-specific fixes, consistency and membership reasoning; missing effect evidence prevents a generic safety claim | Do not build a recommender from these labels |
| Decide whether duplicate-looking calls are safe | Existing idempotency, admission, transaction and step contracts; several reports resolve through those distinctions | Do not claim a new exactly-once method |
| Preserve failure-dependent behavior across administrative repair | Known success-only checkpoint report; PostgreSQL scope not measured in supplied discussion | Run one eight-cell exploratory probe |

The distinction between an unanswered question in these records and a new scientific
question remains essential. The selected measurement can narrow scope and improve a
community reproducer. A positive reproduction alone will not reopen the earlier
method-superiority proposal. Expansion requires a separately justified claim and
independent evidence, as specified in the protocol.
