# History: fresh correctness and replay compatibility

[Walkthrough](../../walkthrough.md) · [Specification](History.tla) · [Measured checks](../../evaluation/model-bridges.md)

## Question and scope

Can a change prevent newly cancelled invocations from dispatching while preserving
commands recorded by the baseline? This finite boundary model separates permission,
a durable activity command, one external effect, and replay of that command.

It is a manual, retrospective abstraction of the three measured code variants and
their single-call probe. It is **not extracted SDK semantics**, a Temporal protocol
model, or a composition/refinement proof connecting Cleanup to History. Both models
represent the same cancellation-policy distinction at different boundaries.

## Inputs and assumptions

Init explores producer B/C/V, replay target B/C/V, and three input classes: approved,
denied, and approved then caller-cancelled during cleanup. The two concrete child
responses collapse to the same abstract input. This gives 27 abstract combinations;
the 36 measured replay cells retain both child responses.

- B swallows the caller cancellation. C propagates it. V propagates it for fresh
  execution and when its recorded patch marker selects the correction during replay.
- V replay without that marker follows the old branch at this point. A non-deprecated
  marker requires version-aware target code. These rules abstract the tested patch
  placement and SDK behavior, not every possible use of version markers.
- Activity retry maximum is one, the activity completes successfully, and the probe
  writes one ledger entry. There are no crash/retry windows, compensation, or rollback.
- Replay reconstructs commands without repeating the already-recorded external
  effect. This is an assumption represented by the transition relation, not a theorem
  about Temporal internals. An injected replay-write fault challenges its invariant.
- The modeled replay begins after the fresh effect stage. Live replacement before
  cancellation, task retry/routing, and incomplete-history prefixes are not modeled.

## State and code correspondence

| Model element | Concrete boundary |
| --- | --- |
| `FreshStop` | B helper versus C outstanding-caller check and V patch-guarded check |
| `Gate` / `permitted` | `_apply_approval_policy` returns and caller may continue |
| `Record` / `command` | `activity_tool_defn` calls `workflow.execute_activity`; retained history has `ActivityTaskScheduled` |
| `marker` | `approval-caller-cancel-v1` non-deprecated marker in V cancellation history |
| `Effect` / `effect` | Successful activity writes the test-only ledger outside workflow memory |
| `PlanReplay` | Target policy chooses its command, using marker presence for V |
| `Compare` / `compatible` | Command equality and marker acceptance for this reduced history |

[Production source](../../../temporal_agent_harness/harness/agent_workflow.py),
[direct patch against the frozen research source](../../upstream/caller-cancellation-research.patch),
[versioned patch](../../upstream/caller-cancellation-versioned.patch), and
[activity probe](../../../tests/activity_upgrade/activity_probe.py) expose the concrete
boundaries. Source hashes remain in the original experiment archives. The new model
and checker have separate hashes in the retained bridge evidence.

## Properties and expected checks

| Property | Expected | Interpretation |
| --- | --- | --- |
| `AuthorizedCommand` | Pass | A command requires accepted approval |
| `NoReplayEffect` | Pass | Replay preserves the single historical effect count under the modeled assumption |
| `BaselineFreshCancellation` | Counterexample | B may command an activity despite caller cancellation |
| `DirectFreshCancellation` | Pass | C prevents the new cancelled invocation's command |
| `VersionedFreshCancellation` | Pass | V prevents the new cancelled invocation's command |
| `DirectPreservesBaseline` | Counterexample | C may omit B's already-recorded command |
| `VersionedPreservesBaseline` | Pass | V retains the modeled B histories |
| `VersionedPreservesUnmarkedCorrection` | Counterexample | Without a marker, V may take the old path for a C history |

The runner adds one duplicate-effect fault and three evidence checks: agreement with
all 36 retained cells, plus two deliberately altered observations that must fail.
TLC explores the finite state space, requiring the named invariant failure in negative
configurations. Tool failures and timeouts never count as model evidence.

## Evidence binding and limits

[The runner](../../scripts/check_history_model.py) reads actual activity events and
patch markers from the frozen histories, ledger counts from the retained files,
accepted status from probe snapshots, and compatibility from the replay records.
It binds these observations to the model's terminal states. It does not supply the
expected compatibility matrix as the model transition relation.

Agreement is retrospective consistency, not out-of-sample prediction. The reduced
command comparison does not establish full SDK command equivalence. The model does
not prove arbitrary-call correctness, exactly-once external effects, rollback safety,
or the correctness of production worker routing. The original empirical migration
limits remain in force.
