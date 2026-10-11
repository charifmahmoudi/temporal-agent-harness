# Screened issue inventory

All 43 unique records from the frozen [CI screen](screen.json), in collection order.
Initial screening uses title/body excerpts; rows marked deep read also used full issue
and discussion. Exclusion means outside these three candidates, not unimportant or
incorrect. See [candidates](candidates.md) for corrections and limitations.

| Issue | Title | Screening disposition |
| --- | --- | --- |
| [temporalio/sdk-python#764](https://github.com/temporalio/sdk-python/issues/764) | Expose Workflow cancel cause/reason | API reason exposure; no demonstrated recovery failure. |
| [temporalio/sdk-python#779](https://github.com/temporalio/sdk-python/issues/779) | [Feature Request] Adding type checking on workflow_execute activity when a variable number of positional args exist in the callable activity | Type checking; incidental keyword match. |
| [temporalio/sdk-python#782](https://github.com/temporalio/sdk-python/issues/782) | [Bug] cancelled timer callback causes asyncio.exceptions.InvalidStateError | Known canceled-timer callback error; supports C3 boundary, not independent durable observer defect. |
| [temporalio/sdk-python#810](https://github.com/temporalio/sdk-python/issues/810) | [Feature Request] Implement proper behavior for `cancelled`, `uncancel`, and `cancelling` of activities and child workflows | Cancellation task API semantics request; no recovery experiment. |
| [temporalio/sdk-python#814](https://github.com/temporalio/sdk-python/issues/814) | [Bug] Python client not able to connect to self-hosted Temporal server via proxy using authorization header | Proxy authentication; outside selected questions. |
| [temporalio/sdk-python#783](https://github.com/temporalio/sdk-python/issues/783) | [Bug] Sticky execution after Worker shutdown causes "Workflow Task Timed Out" | Deep read: cosmetic timeout, reporter confirms other worker works; exclude claimed penalty. |
| [temporalio/sdk-python#794](https://github.com/temporalio/sdk-python/issues/794) | [Feature Request] Make option for OTel workflow spans even if client span not present | Tracing configuration; no recovery failure. |
| [temporalio/sdk-python#848](https://github.com/temporalio/sdk-python/issues/848) | [Bug] Updates conflict with replay | Known update/replay bug; not a new mechanism. |
| [temporalio/sdk-python#971](https://github.com/temporalio/sdk-python/issues/971) | [Feature Request] Configure logging without info on message | Logging configuration; incidental match. |
| [temporalio/sdk-python#994](https://github.com/temporalio/sdk-python/issues/994) | [Feature Request] Worker plugin support for replayers | Replayer plugin configuration; no demonstrated failure. |
| [temporalio/sdk-python#728](https://github.com/temporalio/sdk-python/issues/728) | [Feature Request] Update Ruff target version to 3.9 | Linter target; incidental version match. |
| [temporalio/sdk-python#733](https://github.com/temporalio/sdk-python/issues/733) | [Bug] Unable to run workflows with OpenTelemetry and ddtrace | Tracing dependency/sandbox interaction; distinct dependency failure. |
| [temporalio/sdk-python#743](https://github.com/temporalio/sdk-python/issues/743) | [Bug] ResourceBasedSlotOptions fields not consistent with the underlying Rust implementation | Resource tuner unit mismatch; separate configuration bug. |
| [temporalio/sdk-python#747](https://github.com/temporalio/sdk-python/issues/747) | How to Get the Worker ID Executing the Current Activity? | Worker identity observability request. |
| [temporalio/sdk-python#775](https://github.com/temporalio/sdk-python/issues/775) | [Bug] sdk metrics do not include tags added with "telemetry.global_tags" | Metrics tag regression; outside questions. |
| [dbos-inc/dbos-transact-py#352](https://github.com/dbos-inc/dbos-transact-py/issues/352) | Consistently update `updated_at` for workflow status | Status timestamp consistency; distinct metadata problem. |
| [dbos-inc/dbos-transact-py#404](https://github.com/dbos-inc/dbos-transact-py/issues/404) | Workflow Status Enum for Autocompletion | Typing/autocompletion request. |
| [dbos-inc/dbos-transact-py#425](https://github.com/dbos-inc/dbos-transact-py/issues/425) | Workflow hanging on `get_result` cancellation | C3 known observer cancellation defect, fixed PR427. |
| [dbos-inc/dbos-transact-py#444](https://github.com/dbos-inc/dbos-transact-py/issues/444) | Support non-retryable exceptions for steps | Retry exception policy request. |
| [dbos-inc/dbos-transact-py#640](https://github.com/dbos-inc/dbos-transact-py/issues/640) | BackgroundEventLoop.stop() can hang indefinitely during DBOS.destroy() | Shutdown liveness report; not durable replay-specific; no causal generalization. |
| [dbos-inc/dbos-transact-py#378](https://github.com/dbos-inc/dbos-transact-py/issues/378) | dbos debug can't deserialize non primitive python types used as parameters | Debugger serialization limitation; separate interface issue. |
| [dbos-inc/dbos-transact-py#551](https://github.com/dbos-inc/dbos-transact-py/issues/551) | Support concurrent steps | Deep read: concurrent step support, fixed PR559; no new causal class. |
| [dbos-inc/dbos-transact-py#652](https://github.com/dbos-inc/dbos-transact-py/issues/652) | Enhancement: async-native `recv_async` / `get_event_async` / `sleep_async` to support large concurrent waiter counts | C2 premise retracted in discussion; reject generalization. |
| [dbos-inc/dbos-transact-py#664](https://github.com/dbos-inc/dbos-transact-py/issues/664) | Concurrent asyncio.to_thread calls to @DBOS.transaction lose workflow context inside async workflow | Deep read: async transaction context/support issue, linked async-native work. |
| [dbos-inc/dbos-transact-py#679](https://github.com/dbos-inc/dbos-transact-py/issues/679) | AsyncSQLAlchemyDatasource records PostgreSQL serialization failures as durable errors instead of retrying | Deep read: datasource serialization retry behavior; maintainer confirms fix. |
| [dbos-inc/dbos-transact-py#260](https://github.com/dbos-inc/dbos-transact-py/issues/260) | Workflow recovery failing when using a step with retries configured | Known retry recovery error; another regression without new general claim. |
| [dbos-inc/dbos-transact-py#342](https://github.com/dbos-inc/dbos-transact-py/issues/342) | DBOS Client should not run migrations | Client schema migration responsibility; existing versioning concern. |
| [dbos-inc/dbos-transact-py#405](https://github.com/dbos-inc/dbos-transact-py/issues/405) | Support async workflow management API | Async management API parity request. |
| [dbos-inc/dbos-transact-py#447](https://github.com/dbos-inc/dbos-transact-py/issues/447) | User-request: workflow-level versioning | Workflow-level version selection request; no evaluation. |
| [dbos-inc/dbos-transact-py#471](https://github.com/dbos-inc/dbos-transact-py/issues/471) | User request: make `GlobalParams.app_version` accessible through code | Version introspection API request. |
| [restatedev/restate#2655](https://github.com/restatedev/restate/issues/2655) | Restate partition processor can become stuck after a period of network isolation ends | Jepsen partition-recovery liveness report; known independent testing, not application replay mismatch. |
| [restatedev/restate#3204](https://github.com/restatedev/restate/issues/3204) | Flaky `restate-server::raft_metadata_cluster raft_metadata_cluster_reconfiguration` | Flaky cluster reconfiguration test; requires separate multi-node study. |
| [restatedev/restate#3333](https://github.com/restatedev/restate/issues/3333) | [CLI] `invocations cancel` considers completed invocations when journal retention is enabled | CLI filter includes completed invocations; distinct selection issue. |
| [restatedev/restate#3656](https://github.com/restatedev/restate/issues/3656) | Cancelling invocations in the Backing-Off state seems to have no effect | C1 seed: maintainer explains nondeterminism blocks cooperative cancellation; known contract. |
| [restatedev/restate#3752](https://github.com/restatedev/restate/issues/3752) | CLI command restate invocation cancel MyObject/myKey not working | CLI object-key query bug; distinct selection issue. |
| [restatedev/restate#4364](https://github.com/restatedev/restate/issues/4364) | Encoder arena in InvocationTask retains high-water mark memory for invocation lifetime | C2 separate reported encoder allocation retention; does not validate thread-per-wait premise. |
| [restatedev/restate#4440](https://github.com/restatedev/restate/issues/4440) | Optimize RunCompletionNotification: avoid echoing full payload back to SDK | Protocol payload optimization proposal; no cancellation mechanism. |
| [restatedev/restate#4513](https://github.com/restatedev/restate/issues/4513) | Workflow /output endpoint can return spurious 404 during partition reconfiguration | Deep read: reported stale routing/read result on reconfiguration; standard consistency baseline. |
| [restatedev/restate#4838](https://github.com/restatedev/restate/issues/4838) | 1.7.0-rc.1: `Invalid column family specified in write batch` in journal completion-id index cleanup crash-loops partition processors after upgrade from 1.6.2 | Upgrade column-family/crash-loop report; consequential but requires separate storage migration study. |
| [restatedev/restate#2565](https://github.com/restatedev/restate/issues/2565) | Brief network partitions can cause all ingress requests to time out even after network is healed | Jepsen network recovery report; independent prior test evidence, not a new method. |
| [restatedev/restate#2749](https://github.com/restatedev/restate/issues/2749) | Using restatectl against restate-server running in OrbStack causes panic | Environment/proxy-triggered panic; separate compatibility issue. |
| [restatedev/restate#2762](https://github.com/restatedev/restate/issues/2762) | restatectl <-> restate-server API versioning and compatibility | Admin/client API compatibility request. |
| [restatedev/restate#2765](https://github.com/restatedev/restate/issues/2765) | Support enabling PP state machine features in a multi-node setup | Deep read: coordinated state-machine feature activation; existing version barrier. |

