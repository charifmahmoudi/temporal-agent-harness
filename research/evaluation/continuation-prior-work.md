# Continuation testing: closest baselines and unresolved burden

Primary sources inspected 2026-10-10. This is a focused comparison, not a complete
systematic review. Published claims are attributed to their authors; these tools
have not been benchmarked against our corpus. The
[measured Nexus result](open-recovery-results.md) establishes a test-context
distinction, not a new state-identification principle.

| Source | Existing capability | Consequence for our investigation |
|---|---|---|
| van den Bos and Vaandrager, [state identification for input/output LTSs](https://sws.cs.ru.nl/publications/papers/fvaan/StateIdentification/adg.pdf), §§2–5 | Adaptive tests distinguish incompatible states while allowing outputs outside input/output alternation and partially enabled inputs | Asynchronous outputs and legal-input restrictions alone do not defeat existing distinguishing-test theory |
| Vaandrager and Melse, [CONCUR 2025 fault domains](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.CONCUR.2025.34), abstract and completeness results | Wp/HSI completeness extends to fault domains described by access sequences and bounded additional inputs | A bounded number of continuation steps is not itself a new completeness argument |
| Mohan et al., [CrashMonkey/ACE, OSDI 2018](https://www.usenix.org/system/files/osdi18-mohan.pdf), §§4–5 | Enumerates constrained workloads/persistence points, checks recovered objects, and tests subsequent usability | Crash cuts plus operations after recovery are established; API adaptation alone is insufficient |
| Khan, [Resume Means Resume, 2026 preprint](https://arxiv.org/html/2608.03836v1), §§III,V–VI,IX | Reports explicit persistence contracts, cross-framework deterministic conformance probes, kill-point sweeps, and real process-death controls | Adding recovery contracts, effect ledgers, or several framework adapters is already strongly competed; its claims are not independently validated here |
| Long et al., [LogicHunter, 2026 preprint](https://arxiv.org/html/2607.06195v1), §§3,5.2 | Generates specification-constrained tests with behavioral probes and actively diagnoses failures | Valid inputs and semantic oracles alone are not a new method. Its stated difficulty with complex API interactions/external state is a lead, not a proven gap against all methods |

## What a strong comparison actually requires

Model-based state identification assumes a suitable behavioral model. Applying it
to a workflow requires choices about legal inputs, asynchronous completions,
quiescence, nondeterministic schedules, recovery operations, and observations.
Those choices can be manual; our current fixtures make them manually. An automatic
source translation must justify that it preserves the distinctions used for testing.
The existence of this modelling work does not imply existing tools cannot do it.

Use the same valid continuations and semantic oracle in every selection arm.
Compare all bounded prefixes/cuts, uniform random selection without replacement,
ordinary dependency slicing, upstream regressions extended with the same suffix
grammar, and model-based characterizing tests where an adequate model exists.
Count model-construction and instrumentation effort, invalid trials, compilation,
and execution budget. Do not give only a proposed method a better oracle or a
hand-picked failing suffix. A small grammar may be cheaply exhausted and leave
nothing meaningful to reduce.

## Concrete distinction to investigate

Workflow-visible state may agree while runtime state does not: a wake flag,
pending result-handle identity, or blocked coordination object can differ. A
query returning the same application fields is therefore insufficient evidence
that recovered and live executions have equivalent future behavior. This is a
candidate abstraction pitfall, not a newly discovered theoretical fact.

The needed result would connect a specified abstraction of **application plus
relevant SDK state** to the executable continuations and fault model. A claim of
test reduction needs either a preservation argument for those distinctions or
an explicitly empirical scope. One inspected SDK bug cannot justify a universal
abstraction. In particular, a model omitting SDK wake state could falsely merge
the Nexus states our timer exposes.

## Decision rule

First check whether the ordinary declared suffix sweep catches Nexus. Then test
the separate local-activity identity mechanism using immediate completion. Its
upstream report already has that regression shape. If straightforward baselines
detect both mechanisms at modest cost, record the result and reject an advantage
on this development set. Do not replace that negative result with an unsupported
claim that the advantage will appear at scale.

A surviving proposal requires independently selected cases, frozen predictions,
and a concrete limitation of a well-equipped baseline. None of the reports whose
source or fix we have read is eligible for a blind holdout. The community can use
the retained regressions regardless of whether a scientific contribution survives.
