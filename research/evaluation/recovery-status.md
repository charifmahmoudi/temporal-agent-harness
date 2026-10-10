# Recovery research checkpoint

This page is the current decision record; detailed protocols and raw evidence stay
in their linked files. The objective is an open, reproducible scientific contribution.
Known defects provide development fixtures, not discoveries or blind validation.

**Bounded follow-up completed; external feedback pending:** the
[five-step discovery results](../discovery/results.md) screen three independent engines
and report 18 CI trials across Temporal and Restate. All match the known recovery
contracts; novelty for the cancellation/termination distinction is rejected.
The public review request and conditional evaluation gates are linked from that note.
This does not reopen the stopped method-advantage proposal below.

**2026-10-10 decision: stop expansion of this contribution proposal.** The
[completed question audit](question-audit.md) takes precedence over earlier proposed
next steps. Its [protocol](question-audit-protocol.md) preceded execution and its
[GitHub CI audit](https://github.com/charifmahmoudi/temporal-agent-harness/actions/runs/38058606710)
passed. No candidate currently justifies another scientific experiment. This does
not establish that the field has no open problems; it stops this unsupported proposal.

## Evidence ledger

| Investigation | What is established | What it does not establish |
|---|---|---|
| [#673 reproduction](recovery-investigation.md) and [72-trial pilot](recovery-comparison-results.md) | Known live/replay mismatch; tested heuristic has no advantage over random/regression baselines | General advantage for systematic schedule selection |
| [24-trial Nexus context test](open-recovery-results.md) | Immediate completion masks a defect exposed by a later timer; both cache settings fail on the affected SDK; fixed controls pass | Restart is a necessary cause, or continuation generation is new |
| [12-trial local-activity study](local-activity-results.md) plus 12 corrected-runner checks | Same-version immediate replay exposes the affected decoding signature; remote/fixed controls pass; marker/scorer mistakes are corrected transparently | Silent corruption, recovery of old legacy markers, or universal need for open contexts |
| [48-trial conventional suffix sweep](continuation-results.md) | Ordinary enumeration catches the defect; cached first failures precede replay/eviction; all fixed cells pass | Automatic inference of legal suffixes, a reduction theorem, or a measured advantage |

## Current research judgment

The missing test context is real. Ordinary enumeration catches the Nexus case;
immediate replay catches local-activity identity. A hard selection problem or
advantage over those baselines has not been established.
The inspected [prior work](continuation-prior-work.md) already generates distinguishing
tests and checks behavior after recovery. Our code generates fixtures for a manually
declared grammar; calling that automatic source derivation would overstate it.

Completion, task failures, payload identity, enabled operations, and progress are
different observations. They should be selected from a declared contract. A generic
exception or alarm is not automatically a defect; a completed workflow is not
automatically a sufficient test. SDK state can matter even when application-visible
fields agree. These are useful lessons, not by themselves new theoretical results.

## Gates before reopening

- [x] Reproduce externally reported cases with affected/fixed and matched controls.
- [x] Preserve raw evidence and mechanically rederive results.
- [x] Compare state-identification, crash-testing, and persistence-conformance prior work.
- [x] Complete the conventional suffix sweep and identify the first failure's replay state.
- [ ] Establish a concrete deficiency of a baseline equipped with the same grammar/oracle.
- [ ] State a supported language, fault model, observation contract, and technical claim.
- [ ] Obtain independently selected evaluation cases before adapting a method to them.

A baseline deficiency is relevant to a claimed method advantage, not a universal
requirement for science. An empirical study instead needs a significant estimand,
defined population/sampling, and defensible inference; a theoretical contribution
needs a precise substantive claim. None is established here. The proposed
live/replay/reconstruction taxonomy does not pass merely by adding categories or
cases. No replacement direction has been selected.

If ordinary enumeration handles the development cases cheaply, reject an advantage
on those cases. A larger framework is justified only after evidence identifies what
ordinary enumeration, dependency slicing, or model-based state identification cannot
provide adequately. Neither testing more inspected bugs nor publishing more models
substitutes for that comparison.

## Community reproduction and contributions

Start with the result pages and their `--check` commands. The checks require only
Python's standard library and use committed artifacts; live reproduction uses the
pinned CI workflows and upstream SDK source. Every raw bundle includes run/revision
provenance. Do not infer reproduction success from a green collection job.

A useful submitted case should identify the public report/source revision, legal
workflow and environment, reachable boundary, explicit recovery treatment, executable
continuation, expected observations, and affected/fixed control. Include histories
and logs. Label whether its report/fix has already been inspected. New contributions
should preserve negative and inconclusive results and distinguish a new failure
mechanism from another timing variant of an existing one.

No upstream report or invitation has been sent by this project. No changes are merged.

## Adjacent work and datasets to start from

A preliminary source check finds solid foundations, but no drop-in dataset combining
durable-workflow restarts with independently committed external effects:

| Starting point | What it gives us | Important mismatch with our question |
|---|---|---|
| [UndoBench v1](https://arxiv.org/abs/2610.05622) and its [pinned dataset/code](https://github.com/tradertanmay/undobench/tree/4a25c4fa0f12bb6c79dc6e0e3a8f31deeb6af21e) | Directly studies paired task/recovery trials, duplicate and missing external effects, with 2,880 paired test records. Our [CI qualification](../discovery/baseline-qualification/results.md) independently recomputed those records and located a schema mismatch: the general CLI defaults absent nested effect counts to zero, while the dedicated script and raw effect logs preserve nonzero duplicate/missing counts. | This is a preprint and benchmark artifact, not a live recovery-engine study. The metric/reporting discrepancy is a bounded artifact-reuse finding, not evidence that the benchmark's main result is false or a strong general contribution. Its synchronous harness does not realize every crash boundary; the nearby [Resume Means Resume](https://arxiv.org/abs/2608.03836) work studies crash/resume semantics directly. |
| [RIFL, SOSP 2015](https://sigops.org/s/conferences/sosp/2015/current/SOSP-2015.pdf) | A foundational exactly-once RPC mechanism: durable operation identities and recorded results across crashes/reconfiguration. | It is a mechanism paper, not an agent/workflow recovery dataset. It makes operation identity and retention policy core variables any study must control. |
| [Durable Functions semantics](https://www.microsoft.com/en-us/research/wp-content/uploads/2021/10/DF-Semantics-Final.pdf) | Formal semantics for event-sourced durable functions, replay histories, state, and observational equivalence. | Its model does not by itself characterize a particular engine or an external provider's effect ledger. |
| [WfCommons / WfInstances](https://wfcommons.org/instances) | Hundreds of real scientific-workflow execution instances in a common format, with task graphs, task inputs/outputs, runtime, resource use, and machine information; useful workload/provenance material. | These traces are primarily execution/performance records, not paired fault/recovery trials with effectful external APIs. |
| [ToolSandbox](https://arxiv.org/abs/2408.04682) and its [code](https://github.com/apple-aiml-research/ToolSandbox) | A runnable stateful tool environment, dependent operations, user simulation, and state-based milestone evaluation. | It targets agent tool-use behavior; its published setup does not supply our durable-process restart and provider-idempotency experiment. |
| [Thinkingbox / Thinkingbox-Bench](https://arxiv.org/abs/2608.19741) | A recent stateful business-workflow sandbox with executable checks over final backend state and wrong, missing, or extra effects. | It is close prior work for broad consequential-agent claims. Its reported benchmark is not, by itself, an experiment on durable workflow-engine recovery across ambiguous provider outcomes. |
| [WfBench](https://arxiv.org/abs/2210.03170) | A generator for tunable, reproducible scientific workflow structures and resource profiles. | Synthetic workflow structure does not supply realistic external-side-effect semantics or establish a recovery research question. |

This is a focused starting bibliography, **not** an exhaustive systematic review or a
claim that no closer dataset exists. WfInstances is useful if the question is about
workflow shape or workload realism; ToolSandbox is useful if the question is about
stateful agent/tool actions; Thinkingbox is a close benchmark to read before framing
any broad state-correctness contribution. RIFL and Durable Functions supply essential
systems/semantic baselines. None alone is a sound reason to continue the Medusa case.

A plausible direction to assess (not yet selected or claimed novel) is a controlled
study of the boundary between workflow recovery and provider-side effect guarantees:
vary whether an effect is absent, committed with a lost response, or committed under
an expired operation key; measure duplicate/missing effects and recovery decisions
against provider readback/reconciliation controls. Before any CI experiment, compare
this exact estimand with recent work including stateful business-workflow benchmarks,
ambiguous-outcome recovery studies, and provider idempotency/reconciliation contracts.
If that comparison leaves no consequential unanswered question, stop. The current
Medusa baseline remains only a fixture candidate; it has not qualified as the right
substrate.

## 2026-10-10 nearest-work decision

The full [UndoBench / Resume Means Resume comparison](../discovery/baseline-qualification/results.md#full-nearest-work-comparison-no-experiment-justified) rejects the proposed repair-capability study as already substantially covered: UndoBench tests verify-before-retry, benchmark-wide idempotency, and multiple mutation boundaries; Resume Means Resume measures crash-resume effects with a separate durable ledger. UndoBench also explicitly discloses its initial zero EOR aggregation and forensic correction, so our pinned CLI discrepancy is a useful reuse qualification, not a new metric failure. **No next runtime experiment is justified on this proposal; no scientific contribution is claimed.**