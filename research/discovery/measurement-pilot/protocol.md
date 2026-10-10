# Recovery-evaluator measurement pilot

2026-10-10. Published before evaluator-source inspection and pilot execution.
Purpose: test whether the UndoBench reporting discrepancy transfers to independent
artifacts and changes a substantive conclusion. UndoBench is development evidence
and excluded from the independent denominator. No external outreach.

## Selection and contamination

Discovery queries: "agent benchmark recovery safety effects benchmark github
AgentCrash AgentFailure recovery evaluation"; '"Failing Tools" benchmark github
recovery'; '"ToolEmu" github evaluator safety'. A second engine checked
"agent benchmark evaluation validity missing metrics artifact recovery safety
reproducibility benchmark flaws" and '"Failing Tools" "github" benchmark'.

This is a purposive convenience pilot, not a systematic sample or prevalence
estimate. Search results and project READMEs were read before selection; their
reported outcomes are known. No claim of blinded project selection or independence
from all published knowledge is made.

From the first search's recovery-focused repositories, assess this ordered shortlist:
ARB, agent-error-recovery-bench, DesktopAgentBench, recover-bench, Sabot.
Choose three with public source, retained result records, an offline Python
evaluator usable in Linux CI without paid models, and distinct repository ownership.
Do not choose by observed evaluator defects. README and path inventory establish
initial eligibility; any later failure remains excluded/inconclusive in the ledger,
without replacement beyond this five-project shortlist.

| Project | Pinned revision | Decision |
| --- | --- | --- |
| uujjrmi/agent-reliability-benchmark | 149723ed7dac540a437ee14a34dc5fcf17e7a5e3 | Include: retained frontier results and offline summary |
| rithick007/agent-error-recovery-bench | 585b34e045d7b63b501b5c86a96d14659f31cec1 | Include: retained transcripts and offline metrics |
| Raghava00001/DesktopAgentBench | README screen only | Exclude: advertised Windows-only execution; portability restriction limits this sample |
| Palmerschallon/recover-bench | README screen only | Exclude: README says scoring and baseline results are still in progress |
| Jott2121/sabot | be602555726f3592aaa6cb845685e7853f7fc47a | Include: raw traces and standard-library deterministic scorers |

Repository ownership is evidence of distinct implementations, not proof of unrelated
ideas/authors. Check imports and copied evaluator logic during inspection. ToolEmu
was not in this recovery shortlist; a search snippet exposed an existing scoring
complaint, so it would be contaminated rather than an independent discovery case.

## Claim under test

Exploratory H: a default evaluator can silently convert unavailable measurement
evidence into a favorable outcome or alter a published recovery conclusion.
Alternative: the original UndoBench entry-point issue is isolated, while other
evaluators reproduce their scoped claims.

Distinguish: completion, detection, corrective action, safe abstention and external
effect safety. Only score what each artifact actually records and promises.
Missing effect telemetry is not proof of either safety or a safety-evaluator bug.

## Procedure

1. Inspect each evaluator's declared units, formulas, schemas and retained inputs.
   Publish a subject-specific mapping before execution, including independent
   recomputation and comparison targets.
2. Recompute its published headline from unchanged records with the official
   path and an independently implemented aggregation. Preserve input SHA-256,
   revision, dependency resolution, command exit codes and all outputs.
3. Apply controlled input perturbations only where a mapping makes sense:
   remove a scored field, set it null, duplicate an identified record, and supply
   an empty population. Record rejection, explicit unknown, or numeric output.
   These are robustness probes, not naturally occurring defects.
4. Check substantive impact on the original published records first. Report
   changed counts, denominators, rank ties/reversals or threshold decisions only
   when supported by the artifact's declared comparison. Do not invent a safety
   threshold or rebrand recovery success as external-effect safety.
5. Use the third subject (Sabot) as a procedural transfer check: freeze its
   perturbation policy from the first two before inspecting its evaluator/data.
   Its README has already been read, so this is not a pristine scientific holdout.

All executable work runs in GitHub Actions only. No paid/model calls, fresh agent
campaigns or upstream changes. Source reads and artifact preservation may be local.
A setup failure is inconclusive; bounded environment-only fixes are documented.
Synthetic fixtures may validate arithmetic but cannot supply a population estimate
or a published ranking reversal.

## Scientific gate

Advance only if at least two independent subjects exhibit consequential,
naturally present discrepancies with an explained shared cause, or a separately
justified methodological insight survives the transfer check. A collection of
injected missing-field weaknesses alone fails this gate. Preserve clean results.
Even a positive pilot needs a broader, prospectively sampled study and nearest-work
comparison before a strong contribution claim.

Relevant prior work already studies evaluation validity:
[Log analysis is necessary for credible evaluation of AI agents](https://arxiv.org/html/2605.08545v1),
[HackDetect](https://arxiv.org/abs/2607.22368), and
[Safety, or Just Capability?](https://arxiv.org/abs/2607.28685).
Screened abstracts only at protocol time. Therefore neither "inspect traces" nor
"benchmarks can mismeasure safety" is treated as new here. A full nearest-work
comparison is required before advancing a positive result.
