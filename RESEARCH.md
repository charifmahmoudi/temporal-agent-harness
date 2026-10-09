# Tool-approval verification case study

This fork studies whether Temporal Agent Harness implements a coherent approval
contract when human decisions, automatic evaluations, and closure overlap.
Baseline: `049e01c9d726ef68bff7be857c735723b9801512` (MIT; original copyright retained).

## Initial result and status

The initial specification is manually derived from code, not automatically extracted.
It checks finite one- and two-call configurations and conditional progress. There is
no confirmed implementation defect and no claim of whole-system verification.
Synthetic faults are included to check that the verification detects overwritten
decisions and dispatch without approval; they do not describe original-code defects.

See [implementation correspondence](research/correspondence.md),
[model contract and mapping](research/models/approval/README.md) and the
[verification workflow](.github/workflows/verification.yml).

## Strategy and next experiments

1. Establish a small auditable code-to-model mapping and reproducible CI checks.
2. Validate scheduling assumptions against real Temporal executions; retain the
   existing integration tests alongside controlled method-boundary experiments.
3. Review the implemented policy-change and approve-and-remember extension, its
   projection boundaries, and retained evidence. Inspect upstream history for
   evidence of actual engineering needs.
4. If extraction is pursued, define a restricted Python subset and fail on unsupported
   semantics. The AST drift guard in this contribution is not an extractor.
5. Evaluate findings against full-text related work before making publication claims.

Research value will depend on consequential findings, faithful correspondence, and
transferable lessons. A passing model alone is not sufficient for a conference paper.
Argument-specific approval scope, identity/authentication of operators, external side effects, retries,
Temporal internals, event ordering, callbacks, and policy revocation are not verified
by the initial model.

The [coupled policy extension](research/models/cascade/README.md) adds tool-name
eligibility, remembered approvals, synchronous cascades, and restrictive updates.
Its [interpretation report](research/findings-policy.md) separates intended findings
from their exact-commit CI evidence and the limits of those results.

## Immediate next milestone

The objective is an auditable case study of approval stability under competing
resolutions and changing tool-name policy. The next milestone is independent review
of the abstraction and scenario coverage, followed by broader controlled schedules.

Before enlarging the model, review each transition against its mapped implementation
function and inspect the raw-event evidence for atomicity assumptions. Then add
alternate registration order and controlled evaluator-completion orderings, retaining
counterexample-to-test reproductions for any discrepancy. Acceptance requires passing
model checks, invalid-control rejection, actual Temporal assertions, and ordered trace
witnesses with documented scope. A changed source fingerprint requires mapping review.

A scientific contribution still requires comparison with related work and evidence
that the resulting contract or failure modes matter beyond this harness. Publishable
claims must identify what is new, the practical consequence, and threats to validity;
CI success alone cannot establish those claims.
