# Independent measurement pilot: results and decision

2026-10-10. **The pilot does not justify expanding the UndoBench reporting defect
into a strong scientific-contribution claim.** None of the three new subjects
reproduced that naturally occurring numeric failure. A narrative overstatement,
an incomplete retained pilot, and input-validation weaknesses are useful caveats,
but they do not meet the frozen advancement rule.

[Protocol](protocol.md) · [First-two mappings and transfer policy](mappings.md) ·
[Sabot mapping](transfer-mapping.md) · [Evidence manifest](artifacts.json)

## Execution and population

[GitHub CI run 38069032708](https://github.com/charifmahmoudi/temporal-agent-harness/actions/runs/38069032708)
completed all three jobs successfully on branch commit d2f06f3; actual merge
checkout 5f763a521bc9a5e27034431bc7d2734d31f19c54 and Python 3.12.15 are recorded.
No setup failures, observer fixes, model/API calls, local experiments or outreach.
The primary protocol preceded source inspection; each mapping preceded execution.
No unexpected run was discarded. Automatic repetitions on later PR commits are
validation repetitions, not additional independent subjects.

Three repositories are the units of the exploratory transfer question. Their
record counts below are not independent defects and are not pooled into a safety
rate. Distinct ownership and separate source implementations support operational
independence; no shared evaluator dependency was found in the inspected paths.
This does not establish complete author or intellectual independence.

| Subject | Retained population | Unchanged-data result | Consequence |
| --- | --- | --- | --- |
| ARB | 1,000 unique model/probability/task/trial records | Success/recovery tables agree with independent aggregation; regenerated summary is byte-identical; stored completion agrees with answer comparison | Numeric tables stand; prose needs qualification |
| AERB | 416 unique model/toolset/condition/task records | Audited rates and denominators agree; all stored success flags agree with published task verifiers | Usable only for the recorded partial population |
| Sabot | 825 unique wave-2 cells; 714 in the declared reviewer population | All operator counts agree; all 825 rows rebuild identically from retained files; official check passes | Clean transfer result within the tested scope |

The AERB cross-check reuses its published semantic verifier. The independent
part is metric aggregation, not a new adjudication of task meaning. Similarly,
Sabot's raw reconstruction uses the original scanner; independent arithmetic
does not prove its language-based detection rubric is valid. ARB's final answer
comparison says nothing about intermediate side-effect safety.

## Naturally present caveats

### ARB: narrative, not numerical, disagreement

At failure probability .05, the retained data contains 47/50 LLM successes versus
50/50 for arb-resilient. At .20 the counts are 15/50 versus 28/50. The numeric
tables correctly show these values. Generated prose says the LLM matched the
resilient baseline through .05. Exact equality is unsupported; statistical
equivalence was not tested. The conservative description is 94% versus 100% in
these 50-task samples. This is not a newly discovered table ranking reversal,
nor evidence of a statistically significant performance difference.

### AERB: coverage limitation, not a fabricated completed study

The selected config describes 1,040 episodes; its named retained transcript has
416, leaving 624 absent and none outside the configuration. The runner supports
interrupted/resumed collection. No completed-study claim or missing-data
imputation was established for this artifact. Do not treat this transcript as the
complete configured experiment or infer a representative cross-model result.
The scalar aggregation on records actually present is correct in this check.

### Sabot: the clean result matters

The six operators each have 119 valid reviewer-bearing cells. The other 111
saved cells consist of 39 baseline-failure exclusions and 72 non-reviewer cells
outside that population. Clean false flags use 125 baselines per operator.
The missing-write operator has zero detected and zero recovered among its 119
valid cells, as already reported by its authors; this is reproduced arithmetic,
not our discovery. No table correction is indicated.

## Deliberately perturbed inputs

These probes never replace the original data and do not count as natural defects.

| Perturbation | ARB summary | AERB metrics | Sabot fault_counts |
| --- | --- | --- | --- |
| Remove scored Boolean in first row | KeyError | KeyError | KeyError |
| Set scored Boolean to null | TypeError | TypeError | Coerces null to false; O1 recovered count falls 69 to 68 |
| Duplicate the first identified row | Accepted; row counted again | Accepted; row counted again | Accepted; row counted again |
| Empty population | Empty numeric tables and explicit no-comparison message; generic interpretation text remains | Empty dictionary | Zero counts; official zero-denominator rate renderer says n/a |

No original input had repeated identities. Duplication probes demonstrate trust
in caller-supplied populations, not duplicated physical effects. Sabot's null
coercion in this arm is pessimistic about recovery, not favorable safety
inflation. ARB's unconditional interpretive text on empty input is a robustness
weakness, but it does not create an observed original-data ranking reversal.
All four probes per subject are retained, including rejections and empty results.

## Scientific gate and nearest work

The criterion was two independent, consequential natural discrepancies with an
explained shared cause, or a separately justified methodological advance that
survives transfer. This pilot establishes neither. Do not enlarge it merely to
accumulate bugs, and do not count UndoBench again as independent validation.

[Log analysis is necessary for credible evaluation of AI agents](https://arxiv.org/html/2605.08545v1)
already treats grading artifacts, hidden unsafe behavior, validation and linking
trace findings to reported outcomes. We read its abstract, motivation, principles
and relevant case-study framing. A trace audit alone is not a new method.

[Safety, or Just Capability?](https://arxiv.org/html/2607.28685v1) already examines
metric-dependent conclusions and ranking differences, with explicit panel-size
and construct-validity limits. We inspected its results/discussion and validity
sections. Ranking disagreement across unlike constructs is not itself a defect.

[HackDetect](https://arxiv.org/abs/2607.22368) was screened at abstract level;
HTML retrieval failed. No detailed methodological claim rests on that screen.
This is a focused overlap check, not an exhaustive novelty review.

The practical output is a reproducible audit and sharper reuse rules: preserve
metric denominators, report coverage, validate Boolean fields and record identity,
and derive narrative comparisons from counts. These are established validation
practices; we do not claim a new general algorithm.

## Limits and stopping decision

This convenience sample is small and includes early research repositories.
Selection favored Linux-compatible, model-free offline recomputation and retained
results. The Windows-only README exclusion may discard a usable offline reporting
path; we did not test that project's portability. AERB's incomplete retained run
further limits coverage. Sabot was a procedural transfer check after policy
freeze, not a blinded holdout: its README was already known.

The panel is heterogeneous and does not supply a shared external-effect oracle.
Two subjects primarily measure task/recovery behavior rather than duplicate-effect
safety. Therefore the clean arithmetic checks neither establish that agent safety
benchmarks are generally reliable nor refute a broader measurement-validity problem.

**Stop expansion of this particular contribution proposal.** Keep the verified
UndoBench defect and the independent clean/caveated results as reusable evidence.
A future proposal needs an independently motivated consequential question and a
sampling/evaluation plan that can answer it; this pilot does not supply those by
itself. No new framework, larger model campaign or external contact is initiated.

## Durable evidence

[artifacts.json](artifacts.json) lists exact ZIP IDs, SHA-256 hashes and subject
revisions. [arb.zip.b64](arb.zip.b64), [aerb.zip.b64](aerb.zip.b64), and
[sabot.zip.b64](sabot.zip.b64) retain the original CI archives. Decode base64 to
recover each ZIP. Full reports contain input-file hash inventories, compared
groups, all perturbation outputs, source/observer hashes and official outputs.
[summary.json](summary.json) is a shortened convenience view; omissions are marked
and the ZIP reports remain authoritative. No upstream data or source was edited.
