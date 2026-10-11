# Research-question comparison and decision

2026-10-10. **Decision: no candidate advances to implementation or experiments.**
This is a focused question-selection review, not a systematic review, empirical
replication, or proof that the area has no open problems. The
[selection protocol](protocol.md) was published at
[6cbcb64](https://github.com/charifmahmoudi/temporal-agent-harness/commit/6cbcb64f471e099f885a60233dc0a557aa309f7f)
after initial discovery and before completing the closest-source assessment.

## Where we stand

Earlier rounds produced reproducible engineering evidence, including negative comparisons.
The independent measurement pilot failed its advancement criterion. Those results remain
valuable artifacts but do not establish a strong scientific contribution. We will not
relabel them as one or use another small defect as a reason to restart the same campaign.

The search had been selecting accessible mechanisms before establishing an unanswered,
consequential question. This reset reverses that order. All three questions below concern
decisions an operator actually faces; none earns a contribution claim merely by having
a plausible use case.

| Question | Decision at stake | Strongest existing answer | Disposition |
| --- | --- | --- | --- |
| Q1: recovery after external deduplication expires | Retry, reconcile, or stop a delayed workflow | Retention-aware retry contracts; lease rejection; authoritative reconciliation | Most concrete operational grounding, but generic mechanism already answered; empirical cost study lacks workload evidence |
| Q2: selective revalidation after state or intent changes | Preserve work or restart it | ATR and REVISE directly study this distinction | Reject generic selective-recovery proposal |
| Q3: recovery from ambiguous tool outcomes | Retry, query status, or escalate | Provider guidance and a direct counterfactual agent study | Reject generic ambiguity/observability proposal |

No scores or artificial weighted ranking are used: a failure of novelty or evidence
access cannot be offset by easy implementation.

## Q1 — How much useful recovery remains after duplicate protection expires?

**Task and consequence.** An operator resumes an interrupted order or resource-creation
workflow after a long delay. Reissuing an uncertain request may duplicate an effect;
refusing everything can leave legitimate work incomplete. The relevant decision is which
requests may proceed automatically and which need reconciliation or intervention.

**Public grounding and nearest answer.** Stripe API v1 permits key pruning after at least
24 hours; reuse after pruning creates a new request [S1]. This is not a claim that every
key expires at exactly 24 hours, nor a rule for API v2. PayPal documents endpoint-specific
support and retention [S2]. These are real interface constraints, not observed incident
rates. AWS discusses late requests and identifier lifetime [S3]. RIFL already addresses
unsafe retries after completion-record collection through client leases checked by the
server, reporting uncertainty rather than silently repeating an expired request [S4].
Our client cannot impose RIFL on an unmodified third-party endpoint.

**Candidate claim, before coding.** Existing work establishes how retained identity and
lease rejection protect retries. We would determine the safe-completion versus intervention
cost of composing actual provider contracts over observed recovery delays. Either outcome
would matter: substantial avoidable intervention could motivate integration changes;
negligible exposure or an adequate ordinary policy would argue against them.

**What is actually unresolved here.** We do not know the distribution of delayed recoveries,
whether authoritative reconciliation is available for those operations, or the operational
cost of stopping. No inspected evidence supplies that joint distribution. Merely inserting
an expired key into a simulator answers an already-known question.

**Strongest objection and baseline.** A careful application already persists logical intent,
keeps stable request identity, bounds retry age, uses endpoint-specific authoritative
reconciliation, and stops on unresolved outcomes. This must be the baseline, not blind
retry or a fresh key. A local ledger alone cannot prove a remote commit happened.

**Cheapest discriminating experiment, conditional on evidence.** First acquire a public,
permitted trace cohort containing original dispatch time, recovery time, logical identity,
provider/endpoint contract, reconciliation evidence, and final effect outcome. Freeze its
inclusion rules before outcome inspection. A CI-only paired replay would compare the
ordinary retention-aware policy with an explicitly specified alternative under identical
information. Report duplicates, omissions, safe completions, unresolved outcomes, query
cost, and elapsed recovery time separately. Use synthetic before/after-expiry cases only
as mechanism controls, including delayed in-flight requests and uncertain clock bounds.

**Stop/reopen rule.** No implementation now. Reopen only with a defensible workload cohort
and a decision the baseline does not already settle. If traces lack outcome attribution or
recovery timing, do not replace them with an invented distribution. If the only finding is
that expired deduplication permits duplicates, stop. No production prevalence or benefit
claim can follow from a contract emulator.

## Q2 — Can revalidation preserve useful work without preserving invalid authority?

**Task and consequence.** A paused approval or changed instruction may invalidate only part
of a workflow. An operator wants to retain independent work without releasing a stale action.

**Nearest answers.** ATR explicitly distinguishes harmless version changes from changes
that invalidate a pending decision. It uses executable premises, dependency indexing, and
target-side binding; its controlled evaluation includes a full-scan baseline, durable cells,
and omitted-dependency failures [S5]. REVISE already studies preserving valid branches,
expanding recovery when provenance is incomplete, and revalidating before commit [S6].
CommitGuard and freshness work separately address expired authorization [S7, S8].

**Candidate claim, before coding.** Existing work establishes selective validation and
recovery with explicit dependencies. We would determine whether its end-to-end advantage
persists when obtaining and maintaining trustworthy dependencies is charged. Either outcome
would inform whether a team should instrument dependencies or simply revalidate/restart.

**Residual uncertainty.** Acquisition cost and dependency completeness in a chosen application
are not established by our work. That is a potential empirical question, not a new algorithm.
ATR's developer-authored premises and REVISE's conservative fallback delimit their claims;
they are not defects discovered by us.

**Strongest objection and baseline.** This proposed mechanism is directly occupied, and its
remaining question risks being a routine deployment benchmark. Full premise revalidation,
ordinary optimistic concurrency/conditional writes, suffix recomputation, and full restart
are serious baselines. A proposed selective policy must pay instrumentation, validation,
connector, storage, and recovery costs, not just time an index lookup.

**Cheapest discriminating experiment, conditional on evidence.** In GitHub CI, replay one
independently selected application with revisions that have externally established
dependencies and final-state constraints. Compare full revalidation and conservative
restart/suffix policies against a faithful existing selective method. Measure total work,
invalid effects, unnecessary restarts, and fallback on missing provenance; do not use an LLM
rationale as a completeness oracle. A small deterministic pilot can reject a cost hypothesis,
but cannot establish general model behavior or field prevalence.

**Stop/reopen rule.** Reject building another selective-invalidation runtime. Reopen only
if independent workload evidence makes dependency acquisition a consequential, measurable
decision and distinguishes the question from existing evaluations. We have not established
that condition. A faster lookup on hand-authored graphs is insufficient.

## Q3 — Which observations make ambiguous-outcome recovery actionable?

**Task and consequence.** A timeout leaves an operator unsure whether an external mutation
committed. Retrying and stopping can each be wrong depending on the hidden state.

**Nearest answers.** Stripe's error guidance explicitly treats some server failures as
indeterminate and prescribes reconciliation without substituting a new key [S9].
Sun's *Did It Happen?* directly pairs committed and uncommitted worlds behind identical
timeouts, comparing advice, status queries, and stable idempotency [S10]. Its results
distinguish having information from correctly using it. We read the public full text,
including limitations, rather than treating its title as a complete answer.
EffectMatch also addresses uncertain remote outcomes and continuation blocking [S11].

**Candidate claim, before coding.** Existing work establishes the information problem and
the value of status or idempotency contracts. We would determine whether real reconciliation
interfaces supply evidence sufficient for an ordinary recovery policy at an acceptable cost.
If yes, improve integration; if no, quantify where automation must defer.

**Residual uncertainty.** Provider-specific status can be delayed, incomplete, or unrelated to
the original request. Their prevalence and impact are unmeasured here. Adding a stale-status
toggle to a synthetic benchmark would not alone make the question consequential or novel.

**Strongest objection and baseline.** A deterministic reconciler may solve the specified
task once supplied the required state. Comparing an LLM only with a prompt that says “be
careful” is inadequate. Read-your-writes, transaction status, stable identity, and explicit
unknown states are established techniques.

**Cheapest discriminating experiment, conditional on evidence.** Freeze one publicly grounded
operation and independently labeled histories, including request never accepted, commit with
lost response, delayed observation, and a later unrelated mutation. In CI, compare the
documented deterministic recovery policy with any proposed policy using identical evidence
and budgets. Report correct completion, duplicate effects, omissions, unresolved cases, and
evidence-to-decision errors. If both policies cannot distinguish two histories, attribute
the limit to the interface rather than model intelligence.

**Stop/reopen rule.** Reject a new generic ambiguous-outcome benchmark. Reopen only when a
real interface and workload reveal a decision not covered by existing guidance and the
counterfactual study. Do not conduct more model runs merely to populate another table.

## What changes next

**Do not launch any of these three experiments now.** None satisfies all four admission
conditions in the protocol. Q1 has the clearest public operational grounding, but that
makes it a lead for evidence acquisition, not a selected scientific contribution.

The concrete pivot is from asking whether recovery can fail to asking whether a measurable
operational decision remains poorly supported by existing methods. Before another
implementation round, require one evidence packet: a named workflow, actual observed
recovery/revision histories, a consequence that can be measured, the best existing policy,
and the precise decision that policy leaves unresolved. Public data or user-supplied
authorized traces can supply this; external outreach is not part of this plan.

If such an evidence packet cannot be obtained, change the problem area rather than keep
adding agents, engines, providers, faults, or benchmarks to the current proposal.
This review does not claim all workflow research is exhausted. It establishes that these
three formulations do not justify further experimental investment on our present evidence.

## Execution and limits

- No new experiment, model inference, reproduction, or local test ran in this round.
- The proposed experiments are designs, not executed or preregistered executable protocols.
- Existing CI may trigger on documentation commits; those jobs are not new evidence here.
- Primary papers' reported results are attributed, not independently validated.
- Discovery was purposive and adaptive; abstracts were visible before candidate selection.
- Sources were checked on 2026-10-10. See [source record](sources.md) for reading scope and
  access failures. No claim of exhaustive novelty search or representative incidence.
- No contact, mention, review solicitation, or outreach was sent.
