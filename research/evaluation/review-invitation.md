# External review invitation — draft, not sent

Recipient: not selected. No external contact or maintainer submission has occurred.

Subject: Independent review request: cancellation and durable-history case study

We are seeking independent reproduction and critical review of a bounded case study
in Temporal Agent Harness. The baseline can preserve accepted approval while allowing
a caller-cancelled invocation to dispatch. A direct correction protects tested fresh
executions but conflicts with some old activity histories; a standard versioned
correction has a measured, limited migration scope.

The subject revision is `ccb74997404f6b9fd9f5654ac5a441337581d673` in
https://github.com/charifmahmoudi/temporal-agent-harness . The draft PR is
https://github.com/charifmahmoudi/temporal-agent-harness/pull/1 .

We are not asking for endorsement. We would particularly value attempts to falsify
the cancellation contract, observation-to-model mapping, and history-compatibility
claims. The models are manual and retrospective; no universal refinement, new
versioning method, or formal-method superiority is claimed.

The review packet distinguishes archive auditing, fresh model checking, and fresh
implementation execution. Please choose a scope you can assess, record assistance
and setup failures, and retain categorical results and objections. A response template
is included. We would also welcome advice on whether a prospective second case would
answer a useful question beyond the existing literature.

Before sending: choose the recipient, confirm the desired review scope and whether
the reply may be retained publicly, and add the sender's identity. No deadline,
compensation, affiliation, or agreement is implied by this draft.
