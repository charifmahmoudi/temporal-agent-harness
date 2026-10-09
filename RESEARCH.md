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
3. Extend to policy changes and approve-and-remember only after the initial mapping
   is reviewed. Inspect upstream history for evidence of actual engineering needs.
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
from the exact-commit CI evidence needed to establish them.
