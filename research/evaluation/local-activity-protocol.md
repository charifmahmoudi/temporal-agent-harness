# Local-activity identity: second mechanism protocol

Recorded 2026-10-10 before implementing/executing the adapter. Development report
[Python #1881](https://github.com/temporalio/sdk-python/issues/1881) and comments
have been read. This is not an independent holdout.

Question: does ordinary same-version completed-history replay expose the second
mechanism, without an open-workflow continuation? Reimplement the reported
three-way fan-out, FIRST_COMPLETED wait, conditional `expired` local activity,
and final `finish` activity. Assert every work result equals its assigned index
and the final result equals `finished`. Keep the reported asynchronous immediate
activity bodies; do not introduce a tuned delay to force one grouping.

Run SDK 1.33.0 (tree `ab52fdde33ee8ed193402625bfdba25d240a762d`, Core
`85b71d7ecd4f2bf677fa1cee17f3fbc1ab10f1b9`) and 1.34.0 (tree
`a4c2bb38c3bad43498dfa6bd849e8d85bb684e94`, Core
`e163abd6dc19040064986a63c8b8cf4756ffd320`). The fixed release pins the exact
Core #1616 merge; the affected Core diverges (1 ahead, 49 behind). This is a
release control, not a one-line causal ablation.

Use the same checksum-pinned CLI 1.7.0 dev-server executable as Nexus, Python
3.12, and three repetitions of local and remote activity treatments on each
SDK: 12 workflows with their own same-version replays. Resolve dependencies once
for 1.33.0, save `pip freeze`, then replace only the SDK using `--no-deps` for
1.34.0 and check dependency consistency. Retain histories, replay exception chains,
runtime versions, server hash/version, and source hash. Permit 30 seconds per trial.

Predict affected/local decoding or typed nondeterminism failures, remote controls
passing, and fixed freshly recorded local/remote histories passing. Grouping is
scheduler-dependent, so a non-triggering valid trial is a passing observation,
not discarded or relabelled infrastructure failure. All outcomes must be reported.

Confirm the reported decoding mechanism only when the valid live run passes its
payload assertions and replay's exception chain contains the documented str/bool
type mismatch. Distinguish typed nondeterminism, other errors, wrong results,
and infrastructure alarms. A generic RuntimeError alone is inconclusive.
Inspect retained local-activity markers and conditional activity counts before
interpreting the failure. No silent corruption is presumed: an independent issue
comment reports loud failures for every tried variant, including same-type cases.

Do not claim a fixed SDK repairs affected-version marker histories: #1616 preserves
legacy marker behavior. This experiment tests freshly recorded histories only.
If immediate replay catches the mechanism, it is evidence that a continuation
is not universally necessary, and a conventional oracle can be sufficient here.
If the fixed arm fails, or the affected arm does not reproduce, retain and diagnose
the result before expanding the generator. No superiority or prevalence estimate
is inferred from these twelve development trials.
