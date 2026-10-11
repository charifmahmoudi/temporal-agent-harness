# Approval: decision stability and gate completion

[Case study](../../../RESEARCH.md) · [Properties](../../properties.md) · [Executable specification](Approval.tla)

## Purpose

Approval models already-registered gated calls. Human decisions, automatic evaluation,
and closure compete to settle each call. Decision settlement is separate from caller
completion: superseded evaluator cleanup must finish before gate finalization.

![Approval state dimensions](../../figures/gate.svg)

**Figure 1.** This projection omits evaluator/verdict detail and observer variables.
It shows the normal model; synthetic fault transitions are excluded.

## State

Let $C=\mathrm{Calls}$ be a finite set of calls. A state is

$$v=\langle status,evaluator,verdict,phase,closed,first,resolutions\rangle.$$

| Variable | Domain | Interpretation |
| --- | --- | --- |
| `status[c]` | pending, approved, denied | Current permission decision |
| `evaluator[c]` | running, done, cancelling, stopped, consumed | Abstract evaluator lifecycle |
| `verdict[c]` | none, approve, deny, escalate, error | Recorded evaluator result |
| `phase[c]` | evaluating, cancelling, gate, dispatched, rejected | Caller progress |
| `closed` | Boolean | Shared session closure flag |
| `first[c]` | none, approved, denied | Observer: first accepted decision |
| `resolutions[c]` | 0, 1, 2 | Observer: resolution count; 2 accommodates fault controls |

Initially every call is pending/evaluating, its evaluator is running, no verdict or
first decision exists, resolution counts are zero, and the session is open.

## Transition relation

A prime denotes the successor value. For example, a normal human resolution is

$$
status[c]=pending \;\land\; status'[c]=d \;\land\;
first'[c]=d \;\land\; resolutions'[c]=resolutions[c]+1,
$$

where $d\in\{approved,denied\}$; other calls and lifecycle fields stay unchanged.
The complete assignments are in `Human(c,d)` in the executable specification.

| Action | Enabled when | Effect |
| --- | --- | --- |
| `Human(c,d)` | Call is pending | Accept and record the human decision. |
| `Complete(c,v)` | Evaluator is running | Record task completion and its verdict; leave status unchanged. |
| `Consume(c)` | Caller is evaluating; result is done, call settled, or session closed | If settled/closed, preserve the decision and enter cancellation. Otherwise apply approve/deny, or leave escalation/error pending; enter gate. |
| `Cancelled(c)` | Caller is cancelling | Complete cleanup and enter gate. |
| `Finalize(c)` | Caller is at gate and settled or closed | Deny a still-pending closed call; finish as dispatched or rejected. |
| `Close` | Session is open | Set the closure flag; do not directly change decisions. |

`Next` is the disjunction of these actions. Normal configurations disable `Bypass`
and overwritten human resolutions. Those isolated fault switches test detector
sensitivity and do not describe normal implementation behavior.

## Safety and progress

The [property catalogue](../../properties.md) defines the five state invariants and
`ResolutionProgress`. `FairSpec` additionally assumes, for every call, weak fairness
of Consume, Cancelled, and Finalize. A continuously enabled action must eventually
execute. This represents eventual runner scheduling and evaluator cleanup; it does
not require a human response or a hung evaluator to return without another decision.

## Bounds and correspondence

Safety is checked for one call and two independent calls; progress is checked for one.
These configurations do not establish a parameterized theorem. Calls begin registered;
policy bypass, argument reconstruction, authentication, and external effects are outside
this model. Ordinary malformed results are abstracted as error. The malformed
superseded-result fix has separate implementation regressions.

[Code correspondence](../../correspondence.md) explains the concrete boundaries.
[Evidence and reproduction](../../evidence.md) lists configurations and commands.
