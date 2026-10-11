# Alternative workflow acquisition: adopt an existing returns process

Date: 2026-10-10. Status: workflow specification and instrumentation plan only.
This replaces the suggestion to use our own experiment-publication pipeline as the
research workload. It does not reopen a rejected contribution claim.

## Concrete choice

Use Medusa's existing merchandise-return process as an external application case:
a delivered order, a requested return, receipt with damaged/undamaged quantities,
inventory adjustment, and settlement of the refund obligation.

The [official operator guide](https://docs.medusajs.com/user-guide/orders/returns)
describes customer/admin return requests, receipt, damaged-item handling, refunds and
cancellation. The [order model documentation](https://docs.medusajs.com/resources/commerce-modules/order/return)
and [inventory integration documentation](https://docs.medusajs.com/resources/commerce-modules/inventory/inventory-in-flows)
supply technical follow-up. Sources inspected on 2026-10-10.

These sources establish a real application's supported process. They do not establish
a deployed merchant workload, observed recovery failures, or a research gap.
The operator guide describes receipt-triggered refund behavior and also a separate
outstanding-refund action. Before implementation, resolve the exact behavior against
pinned source and configuration; do not assume receipt atomically settles payment.

## Initial case

An order contains two units of one item. Both were delivered and paid for.
A return requests both units. Receipt records one resellable unit and one damaged unit.
A fixed test merchant policy defines the refund entitlement before execution.
Taxes, fees and shipping are fixed explicitly in the fixture; damaged status does not
implicitly determine financial entitlement.

The required business outcome is:
- One recorded receipt of the two returned units.
- One unit restored to sellable stock; the damaged unit is not sellable stock.
- Exactly the fixture's refund entitlement settled, or a truthful unresolved obligation.
- An order/return view consistent with the independently observed inventory and payment state.

The fixture policy and quantities are our experimental choices, not production observations.
This single case is for qualification, not evidence of generality.

## Baseline and acquisition

Adopt the application's existing APIs, core workflows, configured persistence, recovery
and payment-provider integration. Do not replace its internals with our own recovery
algorithm or disable existing safeguards. Use a deterministic driver initially; an LLM
is unnecessary until a decision actually requires one.

Before any experiment:
1. Pin an upstream commit, dependencies, license, and relevant return/refund source paths.
2. Map each business operation to supported APIs and existing integration tests.
3. Verify the documented normal path in GitHub CI.
4. Confirm that separate observers can see committed inventory and payment effects.
5. Freeze executable scenarios and expected outcomes after resolving configuration semantics.

If a payment test double is necessary, keep it in a separate process with durable state.
Its behavior is an explicit experimental contract, not evidence about a real provider.
Using a real provider sandbox later would validate only that sandbox's tested semantics.

## Observation plan

Record an append-only event stream with:
- case ID, pinned application/configuration revision, and initial-state digest;
- order, return, item, logical operation, attempt and provider transaction identifiers;
- requested and acknowledged operations, timestamps and process lifecycle;
- committed inventory changes and provider-side refund entries;
- reconciliation reads, recovery decisions and unresolved evidence;
- test-driver actions, application retries and manual interventions separately.

Observe final state independently of the driver's return values. Do not infer that an
operation committed merely because its caller reported success. Preserve disagreements
between application state and effect observations.

Measure duplicate/missing effects, correct completion, unresolved obligations, recovery
latency, additional API calls and intervention actions. Intervention counts are not
human effort or monetary cost; those require separate measurements.

## Separate two kinds of evidence

Normal baseline executions determine whether this application can supply the observations
we need. Later controlled executions can introduce interruption, response loss, or repeat
delivery at precisely recorded boundaries. Mark every injected event explicitly.

Keep successes and ordinary recoveries, not just failures. A hand-selected fault matrix
establishes behavior under those conditions; it supplies no natural failure frequency.
No merchant, author, or maintainer contact is required for this acquisition route.

## Scientific decision after qualification

The first deliverable is a runnable, observable existing workflow, not a new contribution.
Ask whether existing recovery can resolve its obligations with the information it retains.
If yes, preserve this as a strong baseline and do not invent a weaker one.
If not, distinguish missing instrumentation, configuration, a known defect, a known
distributed-systems limit, and a genuinely unresolved operational decision.

A novel method or larger experiment requires a separate question and closest-work check.
The earlier question-reset conclusions remain in force. Merely finding a partial refund
or inventory mismatch would not establish novelty.

All execution, qualification and experiments must run in GitHub CI. None has run for this
case yet. This document commits the application choice and acquisition plan, not a claim
of implementation, defects, production relevance beyond the documented process, or results.
