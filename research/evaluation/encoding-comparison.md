# Paired encoding comparison: the local reduction is not yet a contribution

**Result:** the explicit model, the conventional harness executing the source helper,
and the reduced formula agree on all 7,290 declared input cases and 58,320 symbolic
word-comparison cells. This establishes no advantage in expressiveness or correctness
for the proposed reduction. We reject the claim that this local Boolean reduction is,
by itself, the scientific contribution.

The useful technical finding is where the reduction applies: cancellation-count
positivity suffices for the restricted suffix **after cleanup**, but cannot in general
replace the counter **during a prefix containing `uncancel()`**. This is an elementary
abstraction result, not a newly discovered cancellation principle.

## What was fixed before running

The [protocol](encoding-comparison-protocol.json) was published in commit
[`c47873ec31c1916c641cdee3074dd5b4bb1d8e58`](https://github.com/charifmahmoudi/temporal-agent-harness/commit/c47873ec31c1916c641cdee3074dd5b4bb1d8e58)
before comparison implementation. Its SHA-256 is
`7577d5f38f7fc7cc87895aa4924b2f3546242ce24d5d7dc845b249043b081d63`;
the runner refuses a changed protocol. This is an auditable development sequence,
not independent preregistration: the same investigator designed all arms and knows
the original defect.

Predictions included agreement, a counterexample to Boolean tracking during repeated
cancellation, and failures from ignoring patch activation, short-circuiting, or activity
payload identity. None was changed after the first run. The first run had zero arm
disagreements and detected all four deliberately weakened controls.

## Three encodings of the same declared fragment

| Arm | Executed machinery | Hand-authored assumptions |
|---|---|---|
| Explicit reference | Program counter through cleanup, guard, patch, gate, dispatch; event cursor; integer cancellation counter; ordered command cursor | Transition rules and environment contract |
| Conventional harness | Selects B/C/V, compiles and executes the actual `_cancel_and_settle` AST, and drives its coroutine through a declared cleanup suspension | Caller/child/SDK adapters and the gate/dispatch wrapper |
| Reduced suffix | Separately computes the boundary observation and evaluates the conditional formula | Observation map, patch summary, and dispatch formula |

The conventional arm is an ordinary version-dispatch encoding, **not a reproduction
of the published C program-merger tool**, nor an application of that tool's equivalence
theorem to Python. This compares the local reduction with a conventional alternative;
it is not a benchmark against all existing update analyses.

Only the helper body is source-executed. The evaluator, status object, publication,
gate, and activity API are not imported or run. Their boundary behavior is a contract.
Source hashes agree with the [source inventory](repair-boundary.json); these current
research bytes do not replace the frozen activity-study bytes. Corrected and versioned
helpers remain isolated experiment variants.

The adapters do not implement Python task scheduling or Temporal core replay. They
expose the caller counter, a scripted child result, and the declared SDK patch
interface. Agreement cannot validate these shared environmental assumptions.

## Domain and observed results

The Cartesian domain contains 15 cancellation/uncancellation prefixes of length zero
through three, three child completion categories, three variants, two approval values,
nine patch contexts, and three activity signatures: `15 × 3 × 3 × 2 × 9 × 3 = 7,290`.
Eight expected words give 58,320 comparison cells. These are synthetic inputs, not
independent workflows or demonstrated reachable Temporal histories.

| Measurement | Result | Interpretation |
|---|---:|---|
| Outcome, patch-call reachability, and command-word disagreements | 0 / 7,290 | All arms agree within the declared contract |
| Ordered symbolic word verdict disagreements | 0 / 58,320 | Explicit cursor and equality comparisons agree |
| Explicit decision-boundary input keys | 1,944 | Count 0–3 and three child outcomes, with external context fixed |
| Reduced decision-boundary input keys | 324 | Count positivity; caught child outcome omitted |
| Explicitly excluded probes returning unsupported in every arm | 7 / 7 | Checks declared exclusions; does not discover unsupported code |

The sixfold key-count reduction is a domain-cardinality observation at one cut.
Computing the prefix counter is still required. It is neither a measured sixfold
speedup nor a reduction in visited production model-checker states. The conventional
arm could use the same summary. No annotation-effort advantage was measured: all six
primitive-contract clauses and the models were manually supplied.

Exact symbolic word matching is **not Temporal replay compatibility**. It omits
optional/deprecated marker matching, other command attributes, activation jobs, and
the SDK core cursor. Signatures preserve only the declared identity dimensions.
The retained 36-cell real SDK replay study remains separate evidence.

## What the negative controls exposed

| Weakened analysis | Disagreements | Small witness |
|---|---:|---|
| Boolean cancellation tracking throughout the prefix | 324 semantic cases | `cancel, cancel, uncancel` leaves count one, but a Boolean reset loses the outstanding request |
| Unconditional patch call | 1,008 semantic cases | Zero count and fresh activation enabled: the mutant emits a marker the source skips |
| Every fresh patch assumed enabled | 144 semantic cases | Disabled activation takes the old branch; the mutant cancels and emits a marker |
| Command-kind-only comparison | 5,274 falsely accepted word cells | Activity `arg0` is equated with `arg1`; changed options are exercised too |

These aggregate repeated combinations are not distinct bugs. The
[snapshot](encoding-comparison-results.json) retains witnesses, input/script hashes,
and a hash of the full deterministic transcript.

Agreement does not mean predicted behavior is safe. Under the declared fresh-execution
policy “do not schedule with an outstanding caller request,” the reference predicts
288 violating B cases, zero C cases, and 144 V cases. V's violations have fresh
activation disabled or a memoized false patch branch. This follows from the supplied
configuration; it does not show that the retained live study used it. It demonstrates
why the repair guarantee needs an activation assumption. Correctly predicting a
violation is still predicting a violation.

## Why the suffix reduction works, and why it cannot move earlier

Fix variant, approval, SDK context, and activity signature. Consider states just after
cleanup's admitted result has returned or been caught. The child category has no
remaining effect under the contract. The only use of the caller count in the source
suffix is its zero/nonzero test. States with equal count positivity therefore take
the same short-circuit branches, reach the same patch calls, emit the same symbolic
commands, and have the same terminal outcome. Case analysis over B/C/V and patch
context establishes this suffix property for any nonnegative count under the contracts.
The finite run checks its implementation; it does not prove source/runtime correspondence.

Earlier, counts one and two both map to `true`. After one `uncancel`, they become zero
and one, which the C suffix distinguishes. A deterministic transition rule using only
that Boolean and the next operation cannot represent both exactly. The prefix witnesses
are `cancel, uncancel` and `cancel, cancel, uncancel`. This refutes this *specific*
Boolean summary as an exact ongoing representation. It does not rule out sound
nondeterministic overapproximations, richer abstractions, or existing general methods.

The [Python task API](https://docs.python.org/3.12/library/asyncio-task.html) documents
the cancellation counter and `uncancel`. Our adapter does not model pending exception
delivery or version-dependent scheduling. Relating concrete and abstract computations
is established methodology; see
[Cousot and Cousot](https://www.di.ens.fr/~cousot/COUSOTpapers/POPL77.shtml).
Neither this partition nor its counterexample is asserted to be novel.

## Scientific decision

This experiment **rejects a contribution based on the local reduction alone**.
The conventional encoding handles the complete declared domain. There is no demonstrated
new expressive capability, stronger guarantee, or cost advantage. Enlarging this
Cartesian product would not change that judgment.

The broader C3 hypothesis now has a stricter burden: automatically infer a useful
boundary and observation map from source, justify the runtime contracts, and demonstrate
a benefit over existing analyses. Our inventory cannot do that. Its missing capability
is an implementation/proof obligation, not evidence of a gap in the literature.

The next decision should target **source correspondence**. Specify a small supported
Python/SDK language and attempt ordinary dependency analysis plus standard abstraction
to derive this cut and its necessary state. Attempt that baseline first. Only a
concrete limitation requiring a substantive new rule, theorem, or precision/cost
improvement would justify retaining a methodological novelty claim. Independently
authored prospective cases remain necessary later; none was selected or run here.

## Reproduce and inspect

```bash
python research/scripts/compare_repair_encodings.py --check
python research/scripts/test_repair_encodings.py
```

The [runner](../scripts/compare_repair_encodings.py) regenerates all rows and checks the
snapshot. Eleven post-run regression tests add hand-specified outcomes, unknown-input
rejection, command identity/order/multiplicity checks, and a helper-source mutation
detected by the operational oracle. These are same-investigator development checks,
not independent validation. Documentation CI reruns both commands.

No production source, original history, TLA+ model, or earlier frozen result was
changed. No new SDK/server run or full regression execution is claimed here.
