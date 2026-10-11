# What would justify a larger scientific study?

Written while the prospective two-engine probe was running, before reading its
results. This is a conditional study design, not evidence that its hypothesis is true.

The possible contribution is an empirical result about **recovery decisions under
replay incompatibility**. Merely showing that cooperative cancellation needs working
application code is already covered by contracts and public discussion. A utility
script, taxonomy, or repeatable demonstration is useful community work but does not
establish new scientific knowledge on its own.

## Candidate claim and estimand

Hypothesis to justify, not currently assert: an explicit assessment of each recovery
operation's execution dependencies helps operators choose an admissible recovery plan
on previously unseen durable-workflow incidents better than current official guidance.

Primary outcome: fraction of held-out incident tasks for which the selected plan both
terminates or resumes the intended execution and respects the task's stated external
effect/compensation constraints. Correctness must be judged from incident-specific
contracts and independently reviewed expected outcomes. A terminate/kill recommendation
is incorrect when compensation is required and no compensating plan is included.
Record abstention separately; do not improve accuracy by silently excluding hard cases.

This claim is only worth evaluating if independent practitioners can identify actual
decision failures that existing documentation does not adequately resolve. A known
single incident and synthetic mismatches do not establish that premise.

## Gates and proposed design

1. Obtain substantive independent challenge through [review issue #3](https://github.com/charifmahmoudi/temporal-agent-harness/issues/3).
   Require concrete operator decisions, consequences, and nearest prior answers.
   Silence is not validation; inability to establish a missing decision problem stops
   expansion. Ask whether a simpler documentation clarification resolves the issue.
2. If justified, prospectively define an incident population and search window before
   collecting evaluation cases. Broaden beyond the current cancel/replay/version
   keyword sample. Use independently selected public incidents from at least three
   independent engines; collapse duplicate root causes and shared SDK/Core lineages.
   Keep unavailable reproductions and exclusions in the denominator with reasons.
3. Have a second, independent reviewer code failure mechanism, recovery options,
   constraints, and ground truth from full reports and reproductions. Preserve raw
   disagreements and resolve before evaluation. We have not performed this review.
4. Freeze any proposed guide and compare it with official documentation plus ordinary
   debugging, using equal information, tools, time, and access to history. Include a
   compact documentation-only checklist as a strong simpler baseline. Randomize task
   allocation or use counterbalanced disjoint incident sets to avoid learning the same
   answer twice. If human decisions are the claim, automated synthetic scores cannot
   substitute for the appropriate consenting practitioner study.
5. Predeclare a practically meaningful improvement with practitioners, then determine
   sample size from that threshold, clustering, and a development pilot's variability.
   Do not invent a convenient sample size or repeatedly sample until significant.
   Analyze paired differences where appropriate, confidence intervals, missing tasks,
   abstentions, and incident/participant clustering. Report secondary decision time and
   unsafe-recovery rates without selectively promoting a favorable endpoint.

All executable incident reproductions, scoring, and sensitivity analyses belong in
GitHub CI. Protocols, frozen revisions, anonymized/consented review material where
applicable, raw outcomes, and failed setups should accompany the report. No personal
participant data should be fabricated or inferred from GitHub usernames.

## Explicit rejection conditions

- Official guidance predicts the observed behavior and no independent consequential
  decision gap is established: publish the reproduction as a tutorial/evidence note.
- A simpler documentation checklist performs equally well within a prespecified
  practical equivalence margin: reject the added method's claimed advantage.
- Apparent gains vanish on held-out incidents or after controlling information/time:
  reject the generalization or narrow it transparently.
- Independent cases or credible ground truth cannot be obtained: mark the study
  infeasible/inconclusive, not a negative scientific result about the whole field.

The current 18 planned trials are development observations and cannot later become
held-out validation by changing their label.
