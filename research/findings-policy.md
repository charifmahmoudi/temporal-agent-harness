# Findings: approval stability and policy cascades

[Case study](../RESEARCH.md) · [Formal properties](properties.md) · [Evidence](evidence.md)

| Reproduced behavior | Supporting experiment | Practical meaning |
| --- | --- | --- |
| Earlier denial survives remember | evaluator_deny_first; human_deny_first | Policy release does not overwrite settled outcomes. |
| Cascade supersedes ongoing evaluation | remember_first; policy_relax | Accepted policy resolution determines permission; cleanup is a separate stage. |
| Restriction preserves accepted approval | tighten_after_release | Removing eligibility is not retroactive revocation. |
| Remember on denial changes no allow-list | denied_remember | Remember is applied only to an approving decision. |
| Different tools remain isolated | different_tool | Eligibility follows tool name, not merely another call's approval. |
| Initiator publishes first | remember_first; closure variants | Causal publication order can differ from registration order. |
| Close flag alone does not revoke acceptance | close_first | Finalization, rather than flag-setting alone, resolves a remaining pending gate. |

These are bounded model checks and controlled implementation executions. The exact
commit and all counts are in [Evidence](evidence.md), rather than repeated here.

A separate [robustness finding](upstream/superseded-result.md) shows malformed evaluator
output aborting the settled-first path before type validation. The small fix and
before/after regressions are prepared for upstream review. That defect was found by
inspection and targeted execution, not by a TLC counterexample.

The general lesson under investigation is that decision settlement, live eligibility,
publication, cleanup, and external commitment are different events. Conflating them
can misstate the harness's guarantees. Transfer beyond this implementation remains
to be established through the comparative experiment and independent review.
