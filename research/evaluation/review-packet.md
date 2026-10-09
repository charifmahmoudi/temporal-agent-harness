# Independent review and reproduction packet

[Case study](../../RESEARCH.md) · [Protocol](protocol.md) · [Corpus](corpus.json)

## Status and requested expertise

Prepared for an external reviewer; **no independent review or external reproduction
has occurred**. A useful reviewer has TLA+ and asynchronous Python experience, and
was not involved in building these models or tests. Maintainer feedback is a separate
practical assessment. The upstream defect packet is [already prepared](../upstream/superseded-result.md)
but has not been submitted.

## Review questions

| Question | Material to inspect | Evidence requested |
| --- | --- | --- |
| Is the contract faithful? | Approval model, Cascade model, and mapped Python methods | Identify any omitted competing writer or weaker concrete precondition |
| Are atomic boundaries defensible? | Remember/Update handlers and event instrumentation | Check suspending awaits and intermediate publication visibility |
| Does the checker invent behavior? | Schema-2 recorded actions, Hidden relation, and negative controls | Attempt a trace that passes despite an impossible recorded input |
| Is progress overstated? | Fairness clauses and delayed cancellation scenario | Challenge cleanup fairness; distinguish gate permission from external effects |
| Is the comparison fair? | Frozen corpus, collector AST transformation, suite hashes | Verify selection bias disclosure, scoring, and unsupported-case treatment |
| Is the contribution distinct? | Closest trace-validation papers and measured comparison | State the narrowest defensible contribution and missing evidence |

## Reproduction procedure

Use a clean checkout of the reported experiment commit with Java 17, Python 3.12,
and the pinned TLA+ asset. Follow [Evidence](../evidence.md), then run:

```bash
uv run --frozen pytest tests/evaluation/ -q
uv run --frozen python research/scripts/compare_verification.py --jar tla2tools.jar
```

The runner requires git history containing the original upstream commit; a full
clone is needed. Compare categorical outcomes, hashes, and trace counts. Wall times
will vary by machine and are not exact reproducibility targets. Retain the complete
`research/results/comparison/` directory, including failed or inconclusive arms.
Do not amend a frozen fault to make its expected result appear.

## Review record

A completed review should identify reviewer, date, checkout SHA, environment,
commands, observed differences, abstraction concerns, and unresolved objections.
An issue/PR review may hold that record. Do not mark a publication gate complete
without a linked independent record. A maintainer response must be reported in its
own terms; acceptance of a patch does not validate the whole abstraction or novelty.
