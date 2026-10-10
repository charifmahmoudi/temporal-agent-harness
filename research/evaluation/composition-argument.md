# Composition test: the minimal example needs no new rule

**Verdict:** ordinary contract conjunction and elementary implication explain the
example. An unconditional cancellation requirement conflicts with reproducing an old
command. A requirement restricted to newly executing behavior need not conflict.
This example does **not** establish a limitation of existing composition reasoning;
we reject it as evidence for a new composition rule.

## 1. Scope and the three contracts

Consider one gated invocation at its post-cleanup decision point. Fix its identity,
accepted approval, relevant command signature, and position in history. Assume
cleanup terminates, cancellation state is accurately reconstructed, exceptions abort
normal dispatch, and publication/argument preparation introduce no extra commands or
failures. There is no later cancellation before this decision completes. These are
environment assumptions, not properties proved by this note.

Use five Boolean observations:

| Symbol | Meaning at this decision |
|---|---|
| `A` | This invocation's gate is approved; an accepted decision remains unchanged |
| `K` | Its caller has an outstanding cancellation request after cleanup |
| `R` | This particular decision belongs to the recorded prefix being replayed |
| `H` | That prefix requires the relevant activity command at this decision |
| `D` | The new code produces the relevant activity command |

`R` is a specification label for this decision, not a permanent label on an entire
workflow: reconstruction can finish and new execution can follow. `H` abstracts a
fixed zero-or-one command obligation, including identity; it is not a full SDK
history matcher. In fresh execution (`not R`), `H` is irrelevant.

| Component | Assumptions | Guarantee used here |
|---|---|---|
| Approval gate | Stable, correctly identified entry; all relevant dispatch passes through the gate | `D implies A`; cancellation does not revoke accepted approval |
| Corrected cancellation path | Accurate caller identity/count; terminating cleanup; no intervening change; exception propagation prevents dispatch | Unconditional form: `K implies not D`. Intended future-behavior form: `(not R and K) implies not D` |
| Replay boundary | Fixed command identity and history position; reconstruction is required to complete compatibly | `R implies (D = H)` |

The replay row is a requirement for successful reconstruction, not a promise that the
SDK will make arbitrary replacement code satisfy it. Violating it can cause a replay
failure. Likewise, the cancellation rows specify different policies: the scoped form
does not prove that old behavior respected cancellation. It exempts reproducing that
already-recorded behavior from the new policy.

Approval grants permission; it does not entail `A implies D`. If normal-path progress
is required, add `(not R and A and not K) implies D` under the termination assumptions.
The witness below satisfies this additional condition too.

## 2. Minimal conflicting execution

This is an abstract projection of the [retained activity study](activity-results.md),
not a newly collected history or a claim about the shortest possible SDK history.

| Phase | Relevant action | Consequence |
|---|---|---|
| Original B execution | Human approval is accepted | `A = true` |
| Original B execution | Caller cancellation arrives during evaluator cleanup; baseline consumes it | Cancellation does not revoke approval; baseline continues |
| Original B execution | Activity command is recorded, then activity completes | Future replay has a command obligation `H = true` |
| Replacement C replay | Same invocation state is reconstructed and the corrected helper propagates cancellation | At the abstract decision, `A = K = R = H = true`, and C produces `D = false` |

The real study reports B-to-C replay failure for these histories, identifying the
omitted `ActivityTaskScheduled` command at event 19. V reproduces the old branch for
the tested B histories; the tested completed activity is not executed again. These
are prior observations, not a universal no-duplicate-effect guarantee.

At `A = K = R = H = true`, the unconditional cancellation contract requires `not D`,
while replay requires `D`. No decision satisfies both. Gate approval is not the source
of inconsistency. The two instantiated clauses `D` and `not D` form a minimal
unsatisfiable set: removing either leaves a satisfying decision.

This is **not** an example of three jointly satisfied contracts producing an unsafe
composition. The joint unconditional contract has no solution for this input. The
direct correction satisfies one requirement and fails the other.

## 3. Baseline derivation using ordinary contracts

For this finite, acyclic decision, conjoin the guarantees and eliminate `D`.
There is no circular temporal assumption and no liveness proof hidden in the algebra.

**Unconditional cancellation.**

$$\exists D:\ (D\Rightarrow A)\land(K\Rightarrow\neg D)
\land(R\Rightarrow(D=H))
\quad\Longleftrightarrow\quad
(R\land H)\Rightarrow(A\land\neg K).$$

Necessity: `R and H` forces `D`; the other two clauses then force `A and not K`.
Sufficiency: if replaying, choose `D = H`; otherwise choose `D = A and not K`.
The right-hand condition makes every required replay command both permitted and
uncancelled. Thus this is the exact environment restriction for satisfiability of
these three local clauses. It cannot be silently assumed for the known B histories.

**Cancellation restricted to newly executing behavior.**

$$\exists D:\ (D\Rightarrow A)\land((\neg R\land K)\Rightarrow\neg D)
\land(R\Rightarrow(D=H))
\quad\Longleftrightarrow\quad
(R\land H)\Rightarrow A.$$

The same witness suffices. In replay, cancellation's fresh-behavior premise is false;
in fresh execution, the witness suppresses dispatch when `K` holds. Required commands
still need valid approval. This also exposes an identity/authorization mismatch rather
than disguising every problem as cancellation.

These are existential decisions with access to the mathematical inputs. The witness
is **not a deployable repair**, a recommendation to branch on an SDK replay flag, or
a proof that these observations are available at a source repair site. Marker ordering,
patch activation, indistinguishable cohorts, and full command matching remain separate
implementability obligations. The known C-to-V replay incompatibilities remain intact.

## 4. Relation to established assume–guarantee reasoning

Abadi and Lamport's [Conjoining Specifications](https://lamport.azurewebsites.net/pubs/abadi-conjoining.pdf)
provides composition through component specifications and requires the environment
assumptions to be justified. We inspected the introduction, §2.2, §3.5.3, and §5.2
(Theorem 3). Its temporal treatment also prevents a later assumption failure from
excusing an earlier guarantee failure.

Here only the simpler finite conjunction/implication reasoning is needed. We do not
claim to have instantiated all hypotheses of Theorem 3 for the asynchronous Python
implementation, or to have proved liveness, machine closure, or scheduler refinement.
Rather, the proposed minimal obstacle disappears at a level already handled by ordinary
contract reasoning. A more powerful composition theorem is unnecessary for this case.

Reproducing a command and causing a new external effect must remain separate
observations. The retrospective violation cannot be undone by a code change. The
scoped policy can constrain new work while replay preserves historical commands;
it does not retroactively certify the old activity as safe.

## 5. Check and research decision

Run the small finite certificate check:

```bash
python research/scripts/check_composition_argument.py
```

It enumerates all 16 input valuations for each cancellation scope and both possible
decisions: 32 scoped environments, 64 decision valuations. It checks both equivalences,
the constructive witnesses, the conflict, and an unauthorized-history control. The
unconditional form is feasible in 13/16 environments and the scoped form in 14/16.
This checks the displayed algebra; it is not independent validation, automatic source
extraction, or a new SDK experiment. The algebraic proof above explains the result.

**Reject composition alone as the novelty claim for this example.** The earlier
suggestion that it might expose a missing composition rule did not survive this test.
Do not enlarge the model merely to keep that claim alive. A later composition proposal
would need a different, concrete obstacle that existing rules cannot handle adequately.

The scientific objective remains open. The remaining source-correspondence and
restricted-observation questions must still be tested against existing analysis and
synthesis methods; an unimplemented capability in this repository is not evidence of
a literature gap. No independent prospective case is claimed by this note.
