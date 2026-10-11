# Research-question audit and decision

Date: 2026-10-10. [Protocol](question-audit-protocol.md), published as
`c00ebd11100e341046a7d65d21426d83a8849cf6` before the new executable audit.
Evidence cutoff: `72ed3d82bf11871d526043cbee6c0d0ad9b675bc`.

## Decision

**Stop expanding the current continuation/recovery contribution proposal.** The
measured results support narrow reproducible findings, but this audit identifies
no candidate that presently justifies a new scientific experiment. The proposed
mechanism taxonomy is not an established research gap. Automatic source analysis
remains an unspecified possibility, not a surviving demonstrated contribution.

This is a decision about this proposal and its evidence. It does not establish that
durable execution has no open research problems, or that negative results and
replication cannot be scientific contributions. The scientific objective remains;
it has not been replaced with an engineering-report objective.

The key process error was repeatedly proposing a new contribution after a negative
result without first establishing its significance. Freezing another protocol would
make the next experiment more disciplined, but would not supply the missing question.

## Question-by-question adjudication

These explanations and outcomes were known before this audit. The table is
retrospective; its entries are not successful prospective predictions.

| Question | Competing explanations / relevant evidence | Residual uncertainty | Decision |
|---|---|---|---|
| Must Nexus reconstruct before failing? | Reconstruction is necessary versus an accumulated wake flag being checked on a later live activation. Six affected cached timer trials fail before any caller replay or eviction; fixed controls pass. The pinned host checks the flag without a replay condition. | The complete causal path is not established by selective ablation; other workflows may fail on recovery. | Necessity is rejected for this fixture. The narrower result is explained by the known implementation mechanism. |
| Is an open continuation required to reveal these defects? | Universal continuation requirement versus mechanism-specific observations. Local-activity affected histories fail immediate completed replay in both original and corrected collections; remote and fixed controls pass. | Silent same-type corruption and legacy-history repair are not measured. | Universal requirement rejected. Those unmeasured variants are not automatically new scientific questions. |
| Does our selection method improve detection? | The delay heuristic should outperform the supplied alternatives. In the 72-trial pilot it does not; the known regression detects immediately. Ordinary enumeration also detects Nexus at the third supplied grammar entry. | Larger grammars, automatic generation, and total authoring cost were not evaluated. | Claimed advantage rejected on these cases. No extrapolated advantage at scale. |
| Would a live/replay/reconstruction taxonomy add explanatory knowledge? | A transferable relationship versus labels assigned from the known failure reports and fixes. Current cases were selected after inspection; no population, estimand, independent validation set, or informative predictive rule was specified. | Such a study could be designed, but its significance and novelty are unestablished. | Do not start the proposed corpus expansion merely to fill categories. |
| Does the source-to-replay analysis solve a distinct problem? | A sound translation might be substantive; current inventories, manual models, and Boolean feasibility checks do not provide one. The encoding comparison agreed on 7,290 declared cases; contract conjunction explains the minimal composition example. | A supported language, SDK semantics, correspondence theorem, and closest-analysis limitation remain unspecified. | Deferred as an unformulated idea. No analyzer implementation is justified by these results alone. |

## Why the Nexus observation is narrower than a new mechanism

The affected host source, [`workflow_future.rs` at `0689f76`](https://github.com/temporalio/sdk-rust/blob/0689f769ccc440e8d5008d4a623dee3c82a94ff2/crates/sdk/src/workflow_future.rs),
receives an activation, handles eviction, then checks `take_non_sdk_wake()` before
translating the activation. That check has no `is_replaying` precondition. The
[known fix](https://github.com/temporalio/sdk-rust/pull/1353/files) guards polling of
the shared Nexus result future. These source observations account for the direction
of the measured live failure; they do not establish a new recovery principle.

The upstream account emphasized replay of a still-running caller. Our adapted
fixture narrows the necessary conditions and supplies retained evidence. It does
not refute every aspect of that account or establish how frequently the additional
live trigger occurs. We did not measure the moment each wake flag was set or perform
a guard-only forward/reverse intervention. Such ablations could strengthen causal
attribution in this fixture, but currently have no demonstrated contribution beyond
confirming the known fix. They are therefore not scheduled as novelty experiments.

For local activities, [Core #1616](https://github.com/temporalio/sdk-rust/pull/1616/files)
already specifies preservation of activation grouping for newly recorded histories.
Our decoding failure and fresh-fixed controls reproduce that known distinction.
The Python-release comparison changes more than that patch; it supports the observed
release contrast, not isolation of one line as the sole cause. We have not traced
every handle binding or demonstrated silent corruption.

## Closest primary sources and limits of the comparison

Revisited on 2026-10-10. These are targeted readings, not an exhaustive systematic
review or independent replication of the cited tools. Preprints in the earlier
[continuation comparison](continuation-prior-work.md) are not needed for this stop
decision; established sources and our own baseline results already defeat the broad
claims. No claim of absence of prior art rests on a search producing no exact match.

| Primary source and reading scope | What it already addresses | What it does not establish here |
|---|---|---|
| van den Bos and Vaandrager, [State Identification for Labeled Transition Systems with Inputs and Outputs](https://sws.cs.ru.nl/publications/papers/fvaan/StateIdentification/adg.pdf), abstract, §§1–2 and splitting/test construction | Tests that distinguish states under asynchronous outputs and partial inputs | A supplied LTS is not a sound automatic model of arbitrary workflow source or SDK internals; no tool benchmark was run here |
| Mohan et al., [Finding Crash-Consistency Bugs with Bounded Black-Box Crash Testing](https://www.usenix.org/system/files/osdi18-mohan.pdf), §§4–5, especially AutoChecker and workload generation | Bounded valid workloads, persistence points, and reads/writes after recovery | File-system semantics do not directly prove Temporal correctness or the sufficiency of our continuation grammar |
| Burckhardt et al., [Durable Functions: Semantics for Stateful Serverless](https://www.microsoft.com/en-us/research/wp-content/uploads/2021/10/DF-Semantics-Final.pdf), §§3.5, 6.2–6.3, theorem 6.4 | Formal relation between replay histories and stored execution state; observational equivalence in the specified model | The theorem does not certify these SDK implementations, arbitrary Python, or their wake/activation bookkeeping |
| Cirstea et al., [Validating Traces of Distributed Programs Against TLA+ Specifications](https://arxiv.org/abs/2404.16075), abstract rechecked; earlier detailed §4 review retained in the novelty assessment | Instrumentation and constrained trace validation against a formal specification | Passing finite recorded traces does not prove universal refinement or greater detection than tests |
| Finkbeiner, Klein, Metzger, [Live Synthesis](https://arxiv.org/abs/2107.01136), abstract rechecked; earlier definitions 10–11 review retained in the contribution search | Replacement implementations satisfying new requirements and outstanding old obligations | Does not itself supply a code-to-Temporal translation; our supplied finite encoding is not a new synthesis principle |

Searches additionally covered durable workflow replay testing, Temporal Explorer,
state identification, crash consistency, and live updates using two search engines.
Generic “Temporal Explorer” search results were dominated by unrelated temporal
graphs; they were excluded. The earlier pinned source comparison remains the
evidence for that analyzer. Web retrieval of Rust PR #1353 failed; its description
and exact file diff were read through the GitHub connector instead. The local SDK
checkout contains earlier experiment patches, so host-source reasoning used
`git show HEAD:...` at the pinned affected revision, not its modified working file.

## Threats to inference and corrected process

- The distinct bug mechanisms share Temporal SDK Core lineage. Rust and Python
  bindings are not independent workflow engines. Repetitions and alternate timers
  must not be counted as independent mechanisms or evidence of prevalence.
- Test grammar, legal operations, and oracles were manually supplied with knowledge
  of fixes. Renaming that pipeline automatic test derivation would hide its main
  information input. No inspected case can later become a blind holdout.
- Fixed-release controls support defect attribution, but are not a universal causal
  isolation strategy. Instrumented activation details and observer-free detection
  have different evidentiary scope.
- The local-activity marker/scorer mistakes remain recorded alongside the original
  artifacts. Corrected reclassification and validation repeats are not new discoveries.
- Green CI establishes successful checks at a revision. It cannot certify scientific
  novelty. No external scientific review or maintainer assessment is claimed.

The previous proposed requirement to find an unexplained observation is not a
general definition of science. A valuable new measurement, theorem, or method can
qualify without a puzzling anomaly. Likewise, beating a baseline is not mandatory
for every scientific contribution. Here, however, none of those alternative routes
has a sufficiently specified, substantiated claim.

## Execution record and reopening gate

The [CI audit](../../.github/workflows/question-audit.yml) executes the existing raw
evidence auditors and derives factual summaries with input hashes. Its driver is
`7558fc38d5bb62c3d33855ed9fa4eedb5f9bd0f5`.
[Run 38058606710](https://github.com/charifmahmoudi/temporal-agent-harness/actions/runs/38058606710)
passed all six audit commands, including 14 focused evidence tests, and the complete
documentation check. The [exact JSON output](question-audit-ci.json) is retained
from the job log; it records PR head and synthetic merge checkout separately.
The uploaded artifact is `11672725385`, ZIP SHA-256
`75526e92ee0a9afd3e9cfb1de32c6e879a109e3774cb1e13248b88bde8508629`.
Subsequent CI checks compare the factual output with this retained record, excluding
only run/checkout provenance. None of the audited outcomes changed.

The checked collections contain 72 schedule trials, 24 Nexus context trials,
48 continuation trials, and two 12-trial identity collections. Those are repeated
executions of known development mechanisms, not 168 independent defects. Six cached
timer first failures have only live, non-eviction caller activations beforehand;
both identity collections reproduce the same affected-local versus remote/fixed
split. The original measurement corrections remain visible.

No new runtime experiment has been introduced by this audit. Existing PR-triggered
reproductions remain validation repeats of their frozen development cases. All
executable checks in this audit ran in GitHub CI; local work was source reading,
editing, and copying the CI-produced record.

Reopen only with a short candidate statement containing: a consequential unanswered
question; the closest existing answer and its precise limitation; competing
explanations or a precise technical claim; an experiment/proof whose possible
outcomes would change the decision; and an information/sampling plan adequate for
the claimed scope. Publish that statement and predictions before executing any new
experiment in GitHub CI. A different label, another known bug, or a larger test
count does not close this gate. No replacement direction is selected by this audit.
