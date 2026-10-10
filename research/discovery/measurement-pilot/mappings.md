# Subject mappings and frozen transfer policy

2026-10-10; follows protocol c237f3e, before any pilot execution.
First-two source inspection is development knowledge; Sabot evaluator and raw rows
remain unread at this point.

## ARB

Input results/arb_frontier_results.json; unit = (model, failure_probability,
task_id, trial). Official path examples/summarize_results.py and arb.metrics.
Success is mean(success); recovery is mean(recovered) over ALL trials, not
conditional on faults. Independently sum these exact Boolean fields per model/p.
Do not relabel this metric as UndoBench's conditional recovery rate.
Check committed results/summary.md tables and generated text separately.
Stored answer versus expected_answer supplies a limited independent completion
cross-check; it is not an external-effect oracle.

Inspection lead: generated prose unconditionally says the LLM "matched" the
resilient baseline through p=.05 although the committed table is .940 versus 1.000.
Test those counts, preserve the correct table, and classify this as narrative
overstatement if confirmed, not an altered table ranking or safety claim.

Remove success from the first row; set it null; duplicate the first row; empty
the rows list. Exercise official summary construction and retain exception versus
numeric/empty output. Recompute the observed change without calling malformed
inputs a naturally occurring evaluation defect.

## agent-error-recovery-bench (AERB)

Input results/phase2_pilot/transcripts.jsonl, selected because it is the named
retained transcript dataset; do not substitute a separate run's summary.
Unit = (model, toolset, condition, task_id) for this seed/config.
Official path src.eval.metrics.compute_metrics / command-line module.
Independently group successes; condition recovery on primary_fired>0, compound
survival on both fault counters, and capability-conditioned recovery on tasks
solved in the matching model/toolset baseline. Empty denominator is unknown,
not zero. Compare to official three-decimal rates and exact denominator counts.
Check recorded success against the published verifier on retained final states
and answers; this is a consistency cross-check, not a new independent semantic
oracle. Use task files named by the retained config.

Apply the same success removal/null, duplicate-first-row and empty population
probes. Record any missing global model/condition coverage; an incomplete run
is not equivalent to missing per-row fields. These are early research artifacts,
not a representative panel of established benchmarks.

## Frozen transfer policy for Sabot

Without changing the rule after looking at its results: use the documented
wave-2 by-operator offline check, and independently aggregate its saved scored
rows by the documented valid population. Compare detection, reaction, and recovery
separately; preserve clean-baseline false flags and exclusions. Recompute the
official score path where public raw traces permit it.

Use the first saved row in artifact order and its documented scored recovery
Boolean for removal/null, exact duplicate, and empty-population perturbations.
Map field names and official call signatures only after this policy is published.
If the public path cannot accept such data directly, report that probe unavailable
rather than invent a new upstream entry point. Record unchanged results equally.

## Comparison limits

Success aggregation alone cannot verify harmful effects. No universal safety
ranking across these three subjects is defined. Count natural contradictions,
setup failures, documented limitations and injected robustness outcomes separately.
No LLM calls; all numerical execution and validation in GitHub CI.
