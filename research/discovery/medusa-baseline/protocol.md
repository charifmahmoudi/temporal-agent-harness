# Medusa return baseline — qualification protocol

Frozen before execution, 2026-10-10. Application source: medusajs/medusa tag v2.21.2,
commit 020565398e436a2bc65777a3b1ad347b4735d6df (MIT). Runtime packages will be exact
2.21.2 npm releases; resolved lockfile and dependency inventory retained in CI. Source
tag and npm package contents are distinct provenance and not assumed byte-identical.

One deterministic case, no injected failures: a seeded fulfilled/shipped order has
two units at USD25 each, no tax/shipping adjustments, and USD50 captured by a separate
durable payment test service. Request both units back, receive one resellable and
dismiss one damaged, confirm receipt, then explicitly refund USD50 via the existing
refund workflow. Seeded fulfillment is a fixture, not a measured delivery integration.

Read source: core-flows/order/workflows/return/{begin-return,request-item-return,
confirm-return-request,begin-receive-return,receive-item-return-request,
confirm-receive-return-request}.ts; payment/workflows/refund-payment.ts; upstream
integration-tests/http/__tests__/returns/returns.spec.ts. Receipt confirmation adjusts
inventory and payment collection but has no direct refund call. Distinguish receipt
from settlement. The two-unit damage fixture already exists upstream; no discovery claimed.

Required observations: before return stock0; after receipt stock1; return received2,
damaged1; external captures USD50 and refunds0 before explicit refund; after refund one
USD50 refund, matching Medusa payment/refund and order transaction records. Independently
read committed application tables and the payment service ledger. Preserve all stage
snapshots, attempted operations, timestamps, inputs, errors, source/npm provenance and lockfile.

The provider test service is an explicit deterministic test contract, not Stripe/PayPal:
separate Python process, SQLite committed entries, stable operation keys if supplied by
Medusa. No network/provider failure or recovery guarantee is being tested. No production
frequency, human cost, or scientific novelty claim.

Run only in GitHub CI. Dependency/startup/observer problems are qualification failures,
not application defects; retain them and document corrections. Advance to a usable
instrumented baseline only when the stated independent observations agree. Do not expand
to fault injection, repetitions, models or new methods in this round.
