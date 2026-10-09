# Scientific contribution search — iteration 1

Date: 2026-10-09. Starting artifact: `8da75419a2d3e0d097d8082193d539d9ec85f109`.
[Storyline](../storyline.md) · [Earlier novelty assessment](novelty-review.md) · [Pilot evidence](repair-observability.json)

## Objective and result

The objective remains a scientific contribution. The owner explicitly rejected
changing the destination to an engineering experience report. Closing review issue
#2 closed that review thread; it did not establish novelty or independent validation.

This iteration tested the proposed question: can we determine when a behavioral
repair can take effect while respecting recorded commands and future policy?

**Result:** the broad synthesis question is not a defensible novelty claim by itself.
A smaller, executable diagnostic exposes an observation conflict in our retained
histories, but its underlying reasoning is standard. The candidate worth further
investigation is automatic derivation of replay constraints and admissible guard
observations from asynchronous code, with a checkable connection to SDK behavior.
That candidate remains unestablished; no new theorem or transferable method is
claimed by the pilot.

## What the closest work rules out

These are targeted readings, not an exhaustive priority search. Differences in
terminology, implementation language, or application domain do not establish novelty.

| Candidate claim | Closest inspected work | Consequence |
| --- | --- | --- |
| Synthesize a replacement satisfying new requirements and outstanding old obligations | Finkbeiner, Klein, Metzger, *Live Synthesis*, definitions 10–11 and update semantics [S1] | Reject this broad novelty claim. A supplied finite replay monitor can be composed with a policy monitor; merely doing that is not a new synthesis principle. This reduction argument is ours, not a benchmark result. |
| Determine migration eligibility from execution history | Bakshi and Joshi's history-equivalence algorithm [S2] | The paper computes migratable-state mappings in its Petri-net semantics. Ordered SDK replay needs a different representation, but that alone does not establish new mathematics. |
| Derive safe continuations and information requirements from agent execution records | Zheng et al., execution-edit checker, theorem 4 and registration reflection [S3] | Reject a generic claim that deriving obligations or proving information necessity for agents is new. Their input includes registered finite call models and correspondence conditions; our code-to-SDK derivation must be compared explicitly. |
| Synthesize a decision restricted to observable information | Arnold, Vincent, Walukiewicz, controller synthesis under partial observation [S4] | Reject the observation-conflict test below as a new general algorithm or theorem. |
| Preserve old commands using patch markers | Temporal Python versioning [S5] | Established SDK mechanism; generating the known B/V truth table does not establish a new patching technique. |

Absence of the word “Temporal” in a paper is not evidence that its formalism cannot
encode this problem. We have not produced an expressiveness separation from these
methods. In particular, finite models can encode a replay cursor, historical command
constraints, and policy state. The difficult remaining question is how to obtain a
sound model and implementable guard vocabulary from code without supplying the
answer in the abstraction.

## A precise restricted problem

For each retained execution h, let O(h) be a declared tuple of observations available
to a candidate guard and let d(h) be the required Boolean activity-command decision.
For old histories, d is obtained from the recorded activity command. For new
executions, d is supplied by the new cancellation policy. Replay reconstruction is
not a second external effect and does not undo an old effect.

Ask whether one deterministic function f exists such that:

    for every supplied h: f(O(h)) = d(h).

This asks for one implementable decision across a selected cohort. It is stronger
than asking whether each history has some separately chosen acceptable decision:

    exists f, for all h    versus    for all h, exists a decision.

**Elementary criterion, not a novelty claim:** such an f exists on the finite sample
iff no two rows with equal O demand different d. Necessity follows because a function
has one value per input. For sufficiency, assign each observation class its common
required value and extend f arbitrarily to unobserved inputs. That arbitrary extension
is precisely why sample feasibility proves nothing about unseen executions.

The pilot groups rows and returns either a truth table on observed inputs or a
conflicting pair. A separate oracle enumerates complete Boolean truth tables to
cross-check the verdicts. This is not a game solver, a multi-step migration algorithm,
a source extractor, or proof that a returned table can be deployed.

## Executed pilot and concrete witness

[Checker](../scripts/check_repair_observability.py) reads the hash-verified activity
archive through the existing history projection. It deduplicates the 36 replay cells
into **12 distinct histories**, then adds **three explicitly synthetic policy rows**
for fresh approval, denial, and cancellation. Those synthetic rows are requirements,
not newly run experiments. The 36 replay cells are not independent systems.

The declared vocabulary is accepted approval, delivered caller cancellation, and
`patch_branch`. On these completed replay records the last is modeled by the
presence of the recorded patch; on the synthetic fresh cancellation row it is true.
The projection is manually declared, not automatically extracted. It deliberately
does not expose producer labels, workflow IDs, or future commands to the guard.
The latter may be visible to an offline analyst but cannot silently become a guard
input. The full histories and SDK runtime observations are not proven equivalent.

| Record / constraint | Approved | Caller cancelled | Patch branch | Required command |
| --- | --- | --- | --- | --- |
| Retained B, second cancellation raised | true | true | false | emit |
| Retained C, second cancellation raised | true | true | false | omit |
| Retained V, second cancellation raised | true | true | true | omit |
| Synthetic fresh cancellation policy | true | true | true | omit |

The B/C pair has the same declared observations and opposite required decisions.
Therefore **no Boolean guard over this vocabulary satisfies their union**, even
though each cohort separately admits a decision. Both child-response modes occur
in the archive; the reported conflict uses the same response on both sides.

The executable enumeration produced:

| Retained cohort plus three fresh constraints | Smallest sufficient feature set on these rows |
| --- | --- |
| B | approval, patch branch |
| C | approval, caller cancellation |
| B + V | approval, patch branch |
| C + V | approval, caller cancellation |
| B + C + V | none: conflicting observations |

All **40** feature-subset decisions agree with exhaustive truth-table enumeration.
An explicit leakage control supplies the required command as an input; this makes
all rows fit, and is labeled inadmissible. It illustrates why consulting a future
command or a producer label in an offline table can fake an implementable repair.

Positive results concern the activity-command bit only. For example, C + V command
feasibility does **not** say that the current C patch handles V markers or that C→V
SDK replay succeeds. Marker consumption, other commands, workflow termination,
effects, and scheduler behavior remain outside this decision problem. The existing
measured replay matrix remains authoritative for those particular implementations.

This is a retrospective diagnostic, not a new impossibility result about Temporal.
A richer observable vocabulary, persistent controller memory, different patch
placement, trusted routing metadata, or a different repair architecture may change
the answer. Adding metadata today does not establish that old histories contain it.
No full-observation-equivalence claim is made: test workflow names themselves encode
cohort information. No conclusion about arbitrary worker routing follows.

## Did we find a distinguishing example?

We found a distinction between **per-history feasibility** and **one guard using a
restricted observation tuple**. We did not find an example outside established
partial-observation synthesis. The witness therefore passes the “concrete problem”
test and fails the “new theoretical principle” test. Increasing its state space or
renaming it would not repair that novelty failure.

It does improve the next research question: can we automatically derive the right
observation constraints and replay obligations from a real async repair, instead of
manually supplying a truth table or a full registered execution model?

## Surviving candidate and falsifiable target

**Candidate C3:** a sound, explicitly scoped analysis that takes old/new asynchronous
workflow code, an SDK semantics model, a safety policy, and a permitted patch grammar;
it derives replay obligations and available observations, and returns either a
checkable repair condition, an observation-conflict certificate, or “unsupported.”

A possible scientific contribution would be a sound code-to-problem translation with
useful coverage, or a demonstrably more effective analysis of that representation.
Existing synthesis can be its backend. We would have to show why the translation,
coverage, precision, or cost is nontrivial relative to the closest approaches.
A prototype implementation alone would not establish that distinction.

The proposed claim to test is: within a declared fragment, accepted repair conditions
preserve SDK command compatibility and the specified future safety policy, and
rejection certificates identify a real conflict within the declared patch grammar.
“Unsupported” is separate from “impossible.” Soundness requires correspondence for
all executions admitted by the fragment, not a fit to the twelve known histories.
The pilot establishes none of that source-level soundness yet.

Candidate exclusions should initially include reflection, arbitrary Python callbacks,
unbounded dynamically created tasks, and effects with no supplied contract. The
actual supported fragment must be fixed from real code before claiming coverage;
these exclusions are provisional, not a convenient way to hide failed cases.

## Next experiment and stop conditions

1. Derive a decision-point slice from the baseline and corrected helper, gate, and
   activity dispatcher. Enumerate reads, awaits, cancellation edges, command sites,
   and the SDK-provided observations. Mark unsupported operations explicitly. Compare
   that derivation with a hand-reviewed slice before collecting more outcomes.
2. Check whether an existing program-analysis or update-verification tool already
   performs this translation. The Temporal source/history explorer [S6] is a relevant
   implementation lead; its advertised extraction is not evidence of sound synthesis.
3. Implement the smallest translation only if its missing obligation is precise.
   Establish simulation obligations before extending the experiment. A disagreement
   between the slice and a concrete supported run is a failure, not a reason to
   retroactively adjust the frozen prediction.
4. Select independently authored changes under the [prospective protocol](prospective-case.md).
   Compare with cancellation-focused tests plus SDK replay and with the closest
   applicable analysis. Freeze access, predictions, abstentions, effort budgets, and
   scoring. Measure false assurances, supported coverage, diagnostic correctness,
   and engineering effort; report every excluded case.
5. Abandon the claimed methodological contribution if existing methods already supply
   the translation, if supported coverage is negligible, or if the additional analysis
   provides no meaningful precision/cost/diagnosis benefit. One successful second case
   would not establish generality. A negative result must remain in the record.

The [source-boundary follow-up](repair-boundary.md) completes a first manual,
conditional slice and nine reproducible lexical inventories, with implementation-level
comparison of extraction and registration precedents and a dynamic-update merging
comparison. It finds unproved correspondence between the pilot's features and actual
caller/SDK state. Semantic certification remains unsupported. The
[paired encoding comparison](encoding-comparison.md) has now executed that bounded
development step. All arms agree on 7,290 cases; no expressiveness or correctness
advantage is demonstrated. The local Boolean reduction is rejected as a standalone
contribution. C3 still requires source correspondence and a substantive advantage over
ordinary analysis. No second case has been selected or run; no prospective prediction
or external validation is claimed.

## Sources, reading scope, and search record

- **S1:** Finkbeiner, Klein, Metzger, [Live Synthesis, 2021 author version](https://arxiv.org/pdf/2107.01136), §§4–6, definitions 10–11, theorems 4–5; [journal version](https://link.springer.com/article/10.1007/s11334-022-00447-5) overview inspected. Finite-trace and universal update contexts are already explicit. No new implementation experiment with BoSy was run.
- **S2:** Bakshi and Joshi, [History Equivalence, v1](https://arxiv.org/html/2412.08314v1), definitions and algorithms 1–3 inspected, especially transition-trace sets and change regions. Its criterion is not identical to ordered SDK command replay; we do not claim it cannot be extended.
- **S3:** Zheng et al., [Execution Edits, v1](https://arxiv.org/pdf/2608.22928), introduction, theorem 4, §IX, and appendix registration-reflection/rejection-proof passages inspected. The preprint includes correspondence machinery and atomic enforcement; it must not be dismissed as merely accepting an arbitrary agent plan. We did not rerun its Lean artifact or verify every proof.
- **S4:** Arnold, Vincent, Walukiewicz, [Games for synthesis of controllers with partial observation](https://www.labri.fr/perso/igw/Papers/igw-synthesis.pdf), abstract and controller-observation framework inspected. Partial-observation control is established prior art; the pilot claims no advance over its general machinery.
- **S5:** [Temporal Python versioning](https://docs.temporal.io/develop/python/workflows/versioning), patching, deprecation, and replay-testing sections inspected. The pilot's hypothetical guard table is not a replacement for SDK replay.
- **S6:** [Temporal Explorer](https://github.com/stevekinney/temporal-explorer), initially search-result screened; the [follow-up](repair-boundary.md) now pins and inspects command extraction, control-tree construction, and bounded helper traversal. No full-tool execution or repository-wide absence claim is made.

Searches used both available engines, including: `durable workflow replay safe update
automatic synthesis`; `workflow migration history equivalence`; `synthesis update
guards partial observation dynamic software updating replay history`; `Temporal
versioning static analysis replay compatibility`; and exact titles. Some broad
queries returned unrelated replay-attack or operational-migration results; these were
excluded. Publisher access for the partial-observation paper failed; the author PDF
was retrieved. Silence in these searches is not a novelty result.

Reproduce the retained diagnostic (standard library only):

```bash
python research/scripts/check_repair_observability.py --check
```

The JSON records input history hashes, archive hash, script/projection hashes, all
feature subsets, returned tables, and conflicts. Running without `--check` replaces
only this pilot's snapshot, never the original activity evidence.
