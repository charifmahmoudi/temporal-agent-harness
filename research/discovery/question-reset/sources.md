# Source record — question-first reset

Access date: 2026-10-10. Primary material only supports the technical judgments below.
Search-result aggregators and practitioner commentary were discovery aids, not evidence
of novelty or production incidence. Paper outcomes are authors' claims, not our replications.

| ID | Primary source | Inspected scope | What it supports / limit |
| --- | --- | --- | --- |
| S1 | [Stripe idempotent requests](https://docs.stripe.com/api/idempotent_requests) | API v1/v2 distinction, response caching, pruning and parameter comparison | Bounded protection is an explicit API v1 contract; not actual expiry timing or workflow-delay incidence |
| S2 | [PayPal idempotency](https://developer.paypal.com/api/rest/reference/idempotency/) | Retention/support qualifications and timeout example | Support and retention are endpoint-specific; no common provider-wide duration inferred |
| S3 | [AWS: Making retries safe with idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/) | Identifier reuse and late-arriving-request discussion | Identifier lifetime and late requests are established design issues; not a controlled comparative study |
| S4 | [Lee et al., RIFL, SOSP 2015](https://web.stanford.edu/~ouster/cgi-bin/papers/rifl.pdf) | Introduction; completion-record collection, leases, request lifetime and stale-request handling, PDF pages 3–5 | Expiry-safe rejection and detectable ambiguity predate this project; no new lease mechanism claimed |
| S5 | [Lyu et al., From Version Conflicts to Decision Conflicts](https://arxiv.org/html/2609.08015) | Model, dependency semantics, baselines, timing scope, durable/race/omission experiments and results | Direct overlap with selective revalidation; explicit premises and restricted timing matter |
| S6 | [REVISE: Validity-Guided Recovery for Online Revisions](https://arxiv.org/html/2609.00643) | Introduction, public-trace opportunity analysis, recovery description, appendix correctness and efficiency comparisons | Direct overlap with selective reuse and conservative fallback; observed overlap does not establish safe reusable work |
| S7 | [Temporary Authority, Permanent Effects](https://arxiv.org/html/2607.10487v1) | Authority model, controlled invalidation, mitigation framing, limits and open directions | Commit-time authorization and its cost trade-offs are prior questions |
| S8 | [Approved Too Late](https://arxiv.org/html/2608.26306v1) | Abstract, discussion and limitations | Freshness mitigation is already studied; its heuristic horizon is not a universal safety certificate |
| S9 | [Stripe advanced error handling](https://docs.stripe.com/error-low-level) | Server errors, cached errors and reconciliation guidance | Existing deterministic guidance is a required baseline for ambiguous outcomes |
| S10 | [Sun, Did It Happen?, public full-text copy](https://www.researchgate.net/publication/412750365_Did_It_Happen_Counterfactual_Evaluation_of_LLM_Agent_Recovery_from_Ambiguous_Tool_Outcomes), [DOI](https://doi.org/10.21203/rs.3.rs-10730245/v1) | Full-text sections 4.1–4.5, result contrasts, discussion and limitations | Direct counterfactual ambiguity study; synthetic source-grounded templates, not endpoint conformance or production prevalence |
| S11 | [Beyond Approved Actions](https://arxiv.org/html/2609.31301v1) | Execution model, approval/outcome/recovery requirements, ablations and remote-state readback scope | Persistent-outcome checking and continuation control already have direct prior work; remote readback does not undo prior effects |

## Retrieval limits

The version-suffixed HTML routes for S5 and S6 failed. Their unversioned arXiv HTML routes
were readable; this record identifies the inspected URL and date but does not assert
an independently verified immutable version. A later experimental protocol must pin
paper/artifact versions rather than silently assume these URLs are frozen.

The Research Square PDF route for S10 returned 403, and its assets PDF route also failed.
The readable ResearchGate page contains the paper's public full text and DOI; assessment
uses that text, not a third-party review. No author contact was made.

No upstream code/artifact from these newly encountered papers was executed. This is
sufficient to reject broad overlapping claims, not to validate their implementation or
conclude their guarantees apply outside their assumptions.

## Search scope and chronology

The review started from approval freshness, external-retention limits and ambiguous
outcome recovery. Follow-up searches tested stronger objections: selective revalidation,
online revision recovery, lease-based metadata collection, and a direct ambiguous-outcome
agent evaluation. Queries included:

- AI agent human approval stale authorization time of check time of use workflow research
- durable workflow recovery idempotency retention expiration retries payments research
- workflow recovery ambiguous outcomes reconciliation retry decision partial observability research
- selective revalidation agent workflow recovery research
- idempotency retention paper recovery
- RIFL lease garbage SOSP 2015
- Did It Happen Counterfactual agent recovery

Both available search engines were used, with the stronger engine for verification and
primary-source follow-up. At most three research candidates were retained. Finding a
paper's stated limitation was not treated as establishing a worthwhile new contribution.
