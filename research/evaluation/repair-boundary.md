# From cancellation code to a possible scientific contribution

The next research step has narrowed the problem, but has **not established novelty**.
We can locate the repair's inputs in source. We cannot yet certify that the earlier
history-derived inputs denote those same values at the decision point. That missing
correspondence is now a concrete obligation, rather than a general request for a
stronger model.

This report contains a **manually derived, conditional decision slice**, accompanied
by a reproducible lexical inventory. It is not an automatically extracted transition
system. The executable inventory explicitly returns **unsupported for automatic
safety or replay certification**. Unsupported does not mean a repair is impossible.

## The story in code

A human's approval changes the gate's decision. The evaluator can still be unwinding
when the invocation receives cancellation. The baseline helper waits for the evaluator
and discards its exception; that includes a cancellation exception delivered while the
caller is awaiting it. The gate can then finish normally and the dispatcher can request
an activity. The isolated correction checks the **caller's outstanding cancellation
count** after cleanup, including after successful cleanup return. The versioned
correction additionally consults the SDK patch branch so selected old histories retain
their recorded behavior.

These are three distinct facts: permission was granted, the invocation remains active,
and replay requires a particular command sequence. A useful scientific method would
have to derive their relationship from code and declared runtime semantics.

## Source boundary and provenance

The source is [agent_workflow.py](../../temporal_agent_harness/harness/agent_workflow.py)
at the parent research revision `011d7c57b7e2068a0d88abff43e70fd4e9d92177`.
The [inventory](repair-boundary.json) stores exact whole-source and function AST hashes,
locations, awaits, exception handlers, guards, attribute-read syntax, unresolved call
sites, and deferred bodies. Current source bytes differ from the original measured
activity-study bytes; this extraction does not silently replace that frozen evidence.

| Selected definition | Baseline lines | Why it belongs in the decision slice |
|---|---:|---|
| `_handle_tool_approval` | 2267–2302 | Receives a decision and invokes resolution; a remembered approval can trigger a policy cascade |
| `_resolve_and_publish` | 2666–2682 | Calls status resolution and publication; their internal contracts remain dependencies |
| `_run_auto_mode_evaluator` | 2500–2633 | Creates the child task, waits for completion or settlement, and awaits cleanup on the superseded path |
| `_cancel_and_settle` | 282–304 | Contains the exception-swallowing boundary and the isolated repair site |
| `_apply_approval_policy` | 486–634 | Awaits evaluation, waits for gate resolution or close, finalizes approval, and raises on denial |
| `activity_tool_defn.decorator.dispatch` | 3791–3828 | Awaits the gate, prepares arguments, then invokes `workflow.execute_activity` |

The machine inventory covers these six baseline definitions, the two corrected
definitions, and the versioned helper: nine function inventories. Selection is manual.
Names identify lexical definitions, not resolved runtime targets. Attribute reads
include method lookup syntax; they are not an alias-aware data-dependence analysis.
Nested functions and lambdas are recorded as deferred, not treated as eager calls.
Their semantics remain part of the manual review and open obligations below.

## Conditional decision slice

Fix one invocation on the **already-settled, superseded-evaluator path**. Assume
cleanup terminates with normal return, `Exception`, or `asyncio.CancelledError`;
the publication and argument-preparation calls return normally; no additional
cancellation is injected between the helper's decision and dispatch; the remaining
gate wait/finalization returns; and runner/status/task identities are as intended.
These assumptions exclude executions; they are not established by the inventory.

Let `A` be the final gate outcome's `approved` value, `K` mean the captured caller
exists and its `cancelling()` result is nonzero at the post-cleanup check, `W` be
`workflow.in_workflow()`, and `P` the result of the specific patch call **when reached**.
Let `D` mean this dispatch reaches the activity API, not that an external effect occurs.

| Variant | Helper action after cleanup | Conditional dispatch relation |
|---|---|---|
| B: baseline | Returns | `D = A` |
| C: corrected | Raises cancellation iff `K` | `D = A and not K` |
| V: versioned | Raises cancellation iff `K and (not W or P)` | `D = A and not (K and (not W or P))` |

Derivation: the helper catches the listed await exceptions, then B falls through while
C/V evaluate the shown guard. On the superseded path, evaluator return is `None`;
the gate subsequently uses its finalized outcome. A propagated cancellation prevents
normal return through the gate. Normal return permits argument preparation and the
activity API call. In C/V the evaluator also closes the superseded bracket before
re-raising when in workflow. Its publication call therefore needs a contract too.

The formulas are conditional source reasoning, **not an execution model or proof for
all interleavings**. They say nothing about activity completion, retries, external
effect atomicity, exceptions outside the listed set, or unbounded cleanup. No fairness
or termination property follows from an `await` appearing in source.

## The inputs that the earlier pilot did not derive

| Pilot feature or observation | Actual source/SDK dependency | What must be justified |
|---|---|---|
| `approved` from retained evidence | `outcome.approved` after `finalize_approval` | Identity of the gate entry and preservation through concurrent resolution/close |
| `cancelled` from a recorded cancellation signal | Captured caller identity and its cancellation count at a specific program point | Delivery, target, timing, repeated requests, suppression, and any `uncancel()` operations; a signal alone is insufficient |
| `patch_branch` from marker presence or a synthetic fresh row | A reached `workflow.patched` call with SDK memoization and replay state | Patch ID, call reachability/order, marker notification, memoized value, and activation callback configuration |
| Recorded activity command | `execute_activity` with name, arguments, result type, and expanded configuration | Command identity, payload/options, replay position, and distinction from an external write |

The versioned source short-circuits: if `K` is false, it does not call either workflow
predicate; if `W` is false, it does not call `patched`. A single unconditional marker
bit cannot represent this control behavior without a stated abstraction relation.

Inspected Python SDK **1.32.0**, resolved to commit
[`fc6f97a487ed61df9ca5802adb66d8adfcb6df0f`](https://github.com/temporalio/sdk-python/commit/fc6f97a487ed61df9ca5802adb66d8adfcb6df0f),
specifically [`workflow_patch`](https://github.com/temporalio/sdk-python/blob/fc6f97a487ed61df9ca5802adb66d8adfcb6df0f/temporalio/worker/_workflow_instance.py).
It returns a memoized result when available. Otherwise replay/notification/deprecation
can determine the branch; a fresh patch can consult an activation callback; the default
fresh result is true. A true result emits a patch-marker command. Therefore the pilot's
synthetic fresh-cancellation row assumes activation is enabled. This inspection does
not establish core replay matching or callback configuration in every historical run.
The original pilot remains a declared-input consistency experiment, not a derived SDK
guard. Its retained results have not been rewritten.

## What existing methods already supply

| Closest method inspected | Concrete overlap | What this inspection establishes about our candidate |
|---|---|---|
| Temporal Explorer source analyzer | Command and patch discovery, cancellation-scope recognition, structured branches/loops/try/terminal nodes, bounded helper traversal | Source inventory and control-tree construction are already available techniques; those cannot be our contribution |
| Dynamic-update program merging | Transforms old/new programs and update behavior into one program for existing verifiers, with an equivalence result | “Translate updates into verification conditions” is also established; we must compare a specific lowering and its assumptions |
| Execution Edits registration refinement | Typed finite workflow IR, canonical invocation identities, compiled registration, executable refinement predicate and proofs | A finite model-to-registration bridge is not novel by itself; mapping this Python/SDK boundary into such an IR remains an explicit task |

**Inspection scope, pinned where possible:**

- Temporal Explorer commit `ad1200e1f42bdfa86a14bc977799d7223c6cb606`:
  [`workflow-commands.ts`](https://github.com/stevekinney/temporal-explorer/blob/ad1200e1f42bdfa86a14bc977799d7223c6cb606/packages/analyzer/src/workflow-commands.ts),
  [`control-flow.ts`](https://github.com/stevekinney/temporal-explorer/blob/ad1200e1f42bdfa86a14bc977799d7223c6cb606/packages/analyzer/src/control-flow.ts),
  [`interprocedural.ts`](https://github.com/stevekinney/temporal-explorer/blob/ad1200e1f42bdfa86a14bc977799d7223c6cb606/packages/analyzer/src/interprocedural.ts), and workflow-analysis.ts read.
  Helper descent stops at depth one. The control-tree builder excludes cancellation
  scopes and appends otherwise unplaced commands as a rendering fallback. Those
  inspected representations do not themselves supply our required exception/task
  simulation relation. This is not a claim that the repository cannot be extended,
  or that no other part supplies useful checks. We did not execute its analyzer.
- Magill et al., [author draft](https://www.cs.cmu.edu/~smagill/papers/dsu-submission.pdf),
  §§1–2 and §4/theorem 1, figures 6–8 inspected. The transformation renames versions,
  introduces update-state dispatch, and simulates update choices. This is serious prior
  art for the broad translation idea. No Python/SDK encoding or tool run was performed;
  we do not infer inability from its C implementation.
- Execution Edits artifact commit `c3fbdae3675b7e83b9b1e261eea37d9d4c066d60`:
  [`RegistrationRefinement.lean`](https://github.com/eunomia-bpf/agent-check-restore-safety/blob/c3fbdae3675b7e83b9b1e261eea37d9d4c066d60/lean/AuthorityContinuity/AgentHistoryAdmission/RegistrationRefinement.lean)
  read, including `WorkflowIR`, `compile`, `checkRegistration_iff`, and fixtures.
  This module starts with finite promised linearizations and canonical invocation data;
  it proves properties of compilation and registration within that boundary. We have
  not established an extraction from our Python program into it, nor rerun Lean. This
  module-level observation does not erase the paper's other correspondence results.

## Research decision and next discriminating experiment

**Retain C3 only as an unconfirmed hypothesis.** Ordinary extraction, generic update
translation, and finite registration correctness have substantial overlap with prior
work. We have no demonstrated expressiveness separation or superior precision/cost.
The narrower question is whether a compositional treatment of task cancellation and
SDK replay can provide a useful, sound source-to-obligation translation on a declared
fragment. It may turn out to be an application of existing methods.

The next experiment should compare two encodings of this *same* boundary: a direct
operational model of supported task/SDK operations and a conventional merged-program
encoding with an explicit scheduler and replay cursor. Freeze their semantics and
expected exclusions before executing either. Challenge them with: child-only versus
caller cancellation; suppressed cancellation with normal return; repeated cancellation
and `uncancel`; cancellation after the guard; patch call skipped by short-circuiting;
fresh patch activation disabled; old histories with and without a marker; and changed
activity arguments/options. Measure disagreement, false assurances, abstentions, and
manual annotations. These are retrospective development controls, not independent
validation. An independently authored prospective change remains necessary afterward.

Do not call an encoding difference a contribution until an example demonstrates why
the distinction matters, the translation's soundness obligations are discharged, and
the closest existing method is compared fairly. If the ordinary encoding provides the
same guarantees at comparable cost, the methodological novelty claim must be dropped.

## Reproduction and verification

```bash
python research/scripts/extract_repair_boundary.py --check
python research/scripts/test_repair_boundary.py
```

The five focused controls check deferred-body separation, changed exception/guard
visibility, duplicate and missing target rejection, and differing B/C/V input reads.
They validate the inventory's limited contract, not the conditional formulas, the SDK,
or semantic soundness. Regeneration without `--check` updates only this inventory.
No new Temporal histories, full regression run, external review, or prospective result
is claimed in this iteration.
