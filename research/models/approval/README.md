# Approval race model

## Contract

For already registered gated calls, the first accepted resolution stands. A call
dispatches only after an approving outcome. Denial prevents dispatch. Closure denies
an unresolved gate during finalization; it does not revoke an earlier approval.
The validator does not reject a human decision solely because the session is closing:
an approval accepted after the close flag but before finalization can still stand.
This is modeled behavior, not an assertion that closure forbids further dispatch.

An evaluator task finishing is distinct from its verdict being applied. When both
completion and another resolution are observable, the settled branch supersedes
the evaluator. On the ordinary evaluator path, returning and applying its verdict
have no intervening suspension and are modeled together.

## Mapping to agent_workflow.py

| Model | Implementation |
| --- | --- |
| Init | `_WorkflowStatus.register_pending_approval` and evaluator startup in `_apply_approval_policy` |
| Human | `_validate_tool_approval` then the synchronous body of `_handle_tool_approval` (remember=False) |
| Complete | Evaluator task returns approve, deny, escalate, or raises |
| Consume | `_run_auto_mode_evaluator` settled-first branch; ordinary verdict application in `_apply_approval_policy` |
| Close | `_handle_close` sets `_closed` |
| Finalize | Gate wait, `_WorkflowStatus.finalize_approval`, and dispatch permission / `ToolApprovalDenied` |

`first` and `resolutions` are observer variables, not implementation fields. The
source-map manifest fingerprints executable AST of 15 relevant functions. Drift
forces a review; unchanged hashes do not prove correspondence, and changes elsewhere
can invalidate assumptions without triggering this guard.

## Bounds and assumptions

- Safety: one call, plus two independent calls. The two-call configuration checks
  interleavings, not policy cascades or arbitrary numbers of calls.
- All entries begin registered, with auto mode running and no policy exemption.
- Valid, immutable inputs; no UUID collisions; trusted human-update path; valid
  evaluator decision objects. Malformed return values in the superseded branch are
  outside scope. No policy updates, remember cascade, or argument reconstruction.
- Validator and non-yielding handler are treated as one atomic accepted update.
- Cancellation has an explicit cancelling phase. Progress assumes eventual cleanup;
  cancellation-resistant evaluators can invalidate progress conclusions.
- `dispatched` means permission to dispatch, not a committed external effect.
- Progress assumes weak fairness of Consume, Cancelled, and Finalize. It does not assert that
  humans answer or that a hung evaluator finishes without closure/resolution.
- Terminal deadlocks are permitted (`CHECK_DEADLOCK FALSE`); explicit temporal
  properties check progress. No state-space constraints prune reachable states.
- Cancellation completion is nondeterministic. No refinement or overapproximation
  theorem connecting this abstraction to every concrete behavior is established.

## Reproduction

Java 17, Python 3.12, TLA+ tools v1.8.0 (asset checksum enforced by the runner).

```bash
curl -fL https://github.com/tlaplus/tlaplus/releases/download/v1.8.0/tla2tools.jar -o /tmp/tla2tools.jar
python research/scripts/check_source.py
python research/scripts/check_model.py --jar /tmp/tla2tools.jar
uv run --frozen pytest tests/harness/test_tool_approvals.py tests/research/test_approval_boundary.py -q
```

TLC performs parsing/semantic checking before exploration. The runner requires
completed successful checks for Safety, TwoCalls, and Liveness, and exit code 12
with the named invariant violation for each synthetic fault. Tool failures and
timeouts fail the workflow. Results include logs, commit, model/JAR hashes, and Java
version under `research/results/latest`; CI uploads them.

Boundary experiments run the actual validator, decision handler, evaluator-resolution
method, closure method, and finalizer with a controlled scheduling shim. They are not
a Temporal emulator or a refinement proof. Real Temporal traces and their separate model checker are
documented in [the correspondence report](../../correspondence.md). The existing integration
suite supplies separate evidence under the actual Temporal test environment.

## Claims and limits

Passing TLC means these properties hold in the finite abstraction: TypeOK,
DecisionStable, SingleResolution, AuthorizedDispatch, DeniedNeverDispatches; with
fairness, ResolutionProgress. Synthetic Overwrite violates SingleResolution and
Bypass violates AuthorizedDispatch. No parameterized proof, automatic extraction,
exhaustive trace conformance, or implementation-verification theorem is claimed.

Policy cascades are studied separately in [Cascade](../cascade/README.md), which
extends this module without duplicating its gate transitions.
