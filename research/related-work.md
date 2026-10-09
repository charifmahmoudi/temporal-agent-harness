# Related work and contribution boundaries

Search/review date: 2026-10-09. This is a focused primary-source review, not a systematic
literature review or evidence of priority. Search families covered TLA+ trace validation,
implementation refinement, agent runtime enforcement, tool authorization, and human
approval reuse. Recent preprints are separated from published work. Summaries describe
what the sources study; contrasts with this repository are our assessment.

## Closest precedents

| Source and reading scope | Relevant contribution | Consequence for our claims |
| --- | --- | --- |
| [Howard et al., Smart Casual Verification of CCF, NSDI 2025](https://www.usenix.org/system/files/nsdi25-howard.pdf), trace collection/validation, results, and lessons sections | Combines TLA+ model checking with event-constrained implementation traces and reports protocol defects. Discusses aligning atomicity and partial state. | Our trace-checking approach is an application of an established method. Action-bound observations and actionable discrepancies are essential; a small model alone offers little novelty. |
| [Cirstea et al., Validating Traces of Distributed Programs Against TLA+ Specifications, SEFM 2024](https://doi.org/10.1007/978-3-031-77382-2_8); [extended author version v2](https://arxiv.org/html/2404.16075v2), sections 3–6 reviewed | Partial-state and action-parameter constrained trace validation; atomicity alignment and comparative instrumentation experiments. | Both partial observation and action binding are established. Our checker applies this approach to a narrow agent approval contract; it is not a new validation method. |
| [Lamport, An Introduction to TLA+](https://lamport.azurewebsites.net/pubs/simple.pdf), implementation/refinement section | Explains refinement mappings between specifications. | A witness for one finite trace cannot support a universal implementation-refinement claim. We retain that distinction. |
| [Newcombe et al., How AWS Uses Formal Methods, CACM 2015](https://www.amazon.science/publications/how-amazon-web-services-uses-formal-methods), publication screening | Industrial precedent for using formal models to reason about distributed designs. | Applying TLA+ to an existing codebase is established practice, rather than sufficient research novelty. |

## Agent-specific overlap

| Source and reading scope | Relevant contribution | Distinction and limitation of this case study |
| --- | --- | --- |
| [Wang, Poskitt, Sun, AgentSpec, ICSE 2026](https://cposkitt.github.io/files/publications/agentspec_llm_enforcement_icse26.pdf), design/enforcement and discussion sections | A runtime DSL with triggers, predicates, and enforcement, including user inspection. | We examine correctness of an existing asynchronous gate implementation. We do not introduce an enforcement DSL or evaluate harmful-action prevention. |
| [Shi et al., Progent, arXiv:2504.11703v3](https://arxiv.org/pdf/2504.11703), overview and policy-update mechanism | Tool-name/argument privilege policies and deterministic checking of narrowing versus expansion. | Dynamic agent policy is already studied. Our tool-name cascades and preservation of settled resolutions address a narrower implementation contract; this is not equivalent to monotonic confinement. |
| [Winston, Winston, Just, Solver-Aided Verification of Policy Compliance, 2026 preprint](https://arxiv.org/pdf/2603.20449), method and evaluation setup | Encodes tool-use policies as SMT constraints and checks planned calls before execution. | We do not assess the semantic correctness of evaluator decisions or natural-language policy translation. Our nondeterministic verdict abstraction cannot establish either. |
| [Bindschaedler et al., Guarded Commits, 2026 preprint](https://arxiv.org/pdf/2610.00037), guarded-commit design, reuse, and limitations | Binds approvals to recorded evidence, policy versions, and commit-time checks. | Our accepted approval is gate permission, not a transaction-bound commitment. Remembered tool-name approval has broader reuse semantics; neither design should be silently substituted for the other. |
| [Fang, AgentVerify, 2026 non-peer-reviewed preprint](https://www.preprints.org/manuscript/202604.1029), method, evaluation, and limitations | Temporal specifications over agent control flow, runtime monitoring, and post-hoc analysis. | Verifying orchestration rather than neural internals is already an explicit research direction. Our potential value lies in precise implementation correspondence and a reproducible concrete failure, not that framing itself. |
| [FAVA, 2026 preprint](https://arxiv.org/abs/2607.27267), abstract screening only | Permission graphs and an SMT authorizer for context-dependent agent operations. | Relevant authorization overlap; full-text comparison is still open. No claim of superiority is justified. |

## Defensible research question

How can an auditable, bounded model and action-constrained implementation traces expose
mismatches between an agent harness's accepted-resolution contract and its asynchronous
evaluator/cancellation implementation?

The present contribution is a single-system case study: a documented model, stronger
trace constraints, regression-sensitive experiments, and a malformed-result discrepancy
found by challenging an excluded input assumption. The defect was found through code
inspection and a targeted reproducer, not by a TLC counterexample. That provenance
must be reported honestly.

## Review-committee assessment

A submission claiming a new trace-validation method, the first formal agent guardrail,
or whole-system verification should be rejected on the current evidence. A focused
experience report could become credible if it explains the assumption challenge,
retains before/after evidence, quantifies maintenance effort and detection costs, and
establishes transferable lessons. One small defect and a bounded case study do not
alone establish a strong research-track paper.

## Remaining literature work

The extended Cirstea version has now been inspected beyond metadata. Section 4 defines
compatibility as a nonempty intersection of specification behaviors and behaviors
consistent with the partial trace, rather than refinement. It also discusses inverted
invariant checking, action composition, incomplete-log false acceptance, and an
instrumentation-precision experiment. These directly overlap with our method and its
limitations. Our assessment is that action-constrained agent traces alone do not
establish methodological novelty.

Retrieve and compare the full FAVA paper (direct arXiv HTML/PDF retrieval failed on
2026-10-09; its row remains abstract screening); follow references from the closest
papers; inspect comparable framework implementations before asserting prevalence.
A second implementation or parameterized proof would answer different generality
questions. Neither is completed here. There is no exhaustive search, publication
priority claim, benchmark comparison, or claim that absence from this table means
absence from the literature.
