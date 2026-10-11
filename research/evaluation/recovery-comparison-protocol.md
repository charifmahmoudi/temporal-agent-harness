# Recovery scenario selection: frozen development pilot

## Question and scope

Does a simple boundary-oriented schedule order add detection value over a strong
known-regression baseline and seeded random sampling? This is a small development
pilot on the already inspected Temporal #673 family. It cannot establish novelty,
general effectiveness, or independent validation. No new bug is predicted.

Freeze this document and the runner in git before CI results. Do not tune selection
after seeing outcomes. The runner adapts the previously reproduced workflow by
adding an activity latency argument; both releases execute identical Python source.

## Domain, treatments, and budget

The common domain contains eight pairs: activity latency in {0, 0.15} seconds and
signal-to-update delay in {0, 0.05, 0.2, 0.5} seconds. All histories come from actual
server executions. Latencies request schedules; they do not guarantee event order.
A three-second workflow timer and 30-second execution timeout bound each run.

Each method receives four executions per repetition, three repetitions (seeds
0, 1, 2), on each of SDK 1.8.0 and 1.9.0: 72 executions overall.

- **Systematic heuristic:** (0.15, 0), (0, 0.5), (0.15, 0.2), (0, 0), in this order.
  This probes expected overlap, separation, and the completion boundary. It is not
  exhaustive causal exploration and its ordering uses knowledge of this defect.
- **Random:** Python `random.Random(seed).sample(domain, 4)`, without replacement.
  This avoids artificially weakening random selection through duplicate samples.
- **Regression:** (0, 0.5) four times. This is an adapted known-regression schedule,
  not execution of the entire upstream Rust regression suite. It shares the same
  workflow and oracle, giving it direct knowledge of the known triggering condition.

Methods interleave at each budget index, and their order rotates by repetition.
Both SDKs run in one CI job with matched Python dependencies and the identical
server executable; record its SHA-256. SDK 1.8 runs first, so release timing is not
randomized. This is not a single-patch causal experiment.

## Oracle and metrics

The live update may legitimately return false while an activity is in flight. A
valid live trace has one completion when false, two when true, and matching schedule
and completion counts. Only typed `NondeterminismError` on replay counts as a defect.
Other replay errors, missing live preconditions, collection failures, and timeouts
are inconclusive. All attempted trials consume budget, including inconclusive ones.

Primary measures per method/repetition/release: first detection index (right-censored
at four if absent), detection by each budget index, and inconclusive count. Secondary:
number of distinct observed pairs `(update accepted work, first activity completion
before update sequencing event)` and total execution/replay wall time. This coarse
coverage is an observable diagnostic, not a correctness guarantee or full event-order
coverage. Report setup separately and aggregate measured trial costs; no minimizer
is implemented, so no minimization advantage can be claimed.

Retain all complete histories and hashes. Report trial counts separately from distinct
bug families. Three seeds are too few for population-level statistical conclusions.
The fixed release is a negative control, not a proof that every generated scenario
is correct. A lack of systematic advantage ends the efficiency claim for this pilot;
coverage of both busy and idle cases alone does not constitute novelty.

## Decision rule

The known regression is expected to detect this known defect immediately. If it does,
this pilot cannot support a better time-to-detection claim against that baseline.
If systematic ordering differs from random, describe only the measured prefix
coverage/detection difference; do not extrapolate beyond this small known domain.
Before broader claims, require multiple development defect families, a specified
coverage method, and previously uninspected evaluation cases selected before tuning.
