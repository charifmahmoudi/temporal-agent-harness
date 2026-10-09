# From Python execution to model behavior

[Case study](../RESEARCH.md) · [Models](models/approval/README.md) · [Evidence](evidence.md)

## Correspondence question

For a recorded execution, is there a model behavior consistent with its **actual
inputs and ordered partial-state observations**? Both schema-2 checkers answer this
bounded existential question. They do not prove that every Python execution refines
the specification.

## Concrete boundaries

| Implementation boundary | Abstract action | Atomicity rationale / limitation |
| --- | --- | --- |
| Register entry and start evaluator | Init | Modeling begins after registration; startup is excluded. |
| Accepted human handler | Human / Remember | Decision publication and synchronous cascade have no suspending await on the studied path. |
| Evaluator returns or raises | Complete | A probe records immediately before completion without an intervening await. |
| Runner applies result or observes settlement | Consume | Task completion and result consumption are distinct; settled-first branch wins. |
| Cancelled evaluator unwinds | Cancelled | Actual cleanup can suspend; delayed cleanup is exercised. |
| Close handler | Close | Synchronous closure flag change. |
| Finalize entry and permit inline dispatch | Finalize | Finalization is synchronous; this abstracts permission, not external-effect commitment. |
| Install policy and release pending calls | Update | Synchronous replacement and iteration; raw events retain publication order. |

`first`, `resolutions`, `causes`, and `scopeViolation` are model observers. They are
not claimed to be concrete implementation fields. The
[source-map manifest](models/approval/source-map.json) fingerprints 15 mapped methods.
An unchanged hash does not prove correspondence or guard against every relevant change
elsewhere. Updating a mapped method requires a recorded mapping-impact review.

## Projection and trace specification

Snapshots read concrete status and closure; coupled snapshots also read policy and
resolution-event history. Caller completion supplies dispatched/rejected observations.
Inputs record accepted human decisions, policy values, closure, and evaluator results.
Unknown lifecycle fields remain unconstrained rather than inferred.

For observation $O_i$ with recorded action $A_i$, the checker advances its cursor using

$$cursor=i\land A_i\land O_i(v')\land cursor'=i+1.$$

A snapshot without an input uses a stuttering action. Between observations, only
Consume, Cancelled, and Finalize may execute as hidden steps. The checker cannot invent
a human decision, policy change, closure, or evaluator completion to repair a trace.
Coupled validation also binds remembered decisions and the evidenced registration order.

TLC searches for cursor completion by checking the invariant `cursor < trace length`.
Its named violation supplies a successful witness. Completed exploration without that
violation rejects the trace. This inverted success criterion is deliberate; unrelated
errors do not count as witnesses or rejections.

## What the evidence cannot establish

Observers delegate to original methods and add no suspending awaits in production
paths. Instrumentation equivalence is nevertheless unproven. Synchronous model actions
hide intermediate publications, while raw events preserve them for separate assertions.
Partial snapshots and hidden internal actions leave multiple possible model witnesses.

The abstraction assumes valid identities, trusted inputs, and eventual cleanup for
progress. It excludes replay, arbitrary call count, authentication, and external effects.
The [malformed-result finding](upstream/superseded-result.md) challenged an earlier input
assumption. Its fix preserves the valid-input model transitions; its separate regressions
do not turn trace validation into a refinement proof.
