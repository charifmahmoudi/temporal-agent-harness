# Independent review quickstart

[Review packet](review-packet.md) · [Response template](review-response-template.md) · [Novelty assessment](novelty-review.md)

## Frozen subject and scope

Review subject: `ccb74997404f6b9fd9f5654ac5a441337581d673` in
https://github.com/charifmahmoudi/temporal-agent-harness . All eight author CI workflows
passed at that revision. This does not count as independent reproduction.

The later review driver only orchestrates existing commands and captures logs; the
subject itself stays at that exact revision. It labels no run independent. A human
response must disclose prior involvement, assistance, environment, and review scope.

| Stage | What you actually do | What success can establish |
| --- | --- | --- |
| `audit` | Validate retained evidence, generated documentation, and source mapping | Archive/internal consistency, not fresh reproduction |
| `models` | Run TLC on Approval, Cascade, Cleanup, cancellation traces, and History | Fresh reproduction of finite model results using retained concrete traces |
| `cancellation` | Execute baseline/corrected cancellation studies, same-version replay, and corrected harness regressions | New concrete cancellation evidence |
| `activity` | Generate fresh activity runs, replay matrix, live replacements, and V regressions | New concrete upgrade/effect evidence |

Critical abstraction review is a separate task. Passing all commands does not decide
whether the contract, atomic steps, observation completeness, or novelty are adequate.

## Setup

Use a disposable Linux environment with Java 17, Python 3.12, git, curl, and uv 0.12.23.
Live stages need network access to acquire the SDK test server and ordinary local
process/network permissions. Do not use production credentials or a production
Temporal service. Dependency versions come from the subject's frozen uv.lock.

From a parent directory you control:

```bash
git clone https://github.com/charifmahmoudi/temporal-agent-harness.git review-tools
cd review-tools
git checkout research/approval-verification
git worktree add --detach ../review-subject ccb74997404f6b9fd9f5654ac5a441337581d673
cd ../review-subject
uv sync --frozen --python 3.12
cd ..
curl --fail --location --retry 3 https://github.com/tlaplus/tlaplus/releases/download/v1.8.0/tla2tools.jar -o tla2tools.jar
```

Expected JAR SHA-256:
`7beec0f04818732a62fa193731711a99aa4f11279499b2360a7d156c519ea78d`.
The model runners enforce it. Record `git -C review-tools rev-parse HEAD` too, since
the review driver may evolve separately from the frozen subject.

Inspect the plan before execution:

```bash
python review-tools/research/scripts/reproduce_review.py --subject review-subject --stage plan
```

Then run the chosen stages; replace the reviewer value with your identity:

```bash
python review-tools/research/scripts/reproduce_review.py --subject review-subject --stage audit --reviewer 'REVIEWER' --output review-output/audit
python review-tools/research/scripts/reproduce_review.py --subject review-subject --stage models --jar tla2tools.jar --reviewer 'REVIEWER' --output review-output/models
python review-tools/research/scripts/reproduce_review.py --subject review-subject --stage cancellation --python review-subject/.venv/bin/python --reviewer 'REVIEWER' --output review-output/cancellation
python review-tools/research/scripts/reproduce_review.py --subject review-subject --stage activity --python review-subject/.venv/bin/python --reviewer 'REVIEWER' --output review-output/activity
```

Output directories must be new. Preserve failed runs; use a new subject worktree for
repeated live stages rather than overwriting measurements. A nonzero exit, timeout,
or missing executable is a failed/inconclusive attempt, never a detected model defect.
Each command has a 30-minute timeout; no total run-time guarantee is made.

## Compare categorical outcomes

- Cleanup: six expected checks; baseline cancellation invariant violation and blocked
  progress are required negative results. These are not unexpected tool failures.
- Cleanup correspondence: four matches, eight model rejections, three malformed-record
  rejections. This stage consumes retained observations, not newly collected ones.
- History: twelve expected TLC results, including agreement with 36 retained cells.
- Cancellation: 23 tests per variant, sixteen completed-history replays per variant,
  and 375 existing harness regressions against C. Characterization tests pass when
  they reproduce the baseline defect; that is not a baseline correctness claim.
- Activity: 12 fresh runs, 36 replay cells (26 compatible and 10 explicitly
  nondeterministic), eight live replacements, and 375 V regressions. Two live B → C
  post-activity cases must record nondeterministic workflow-task failure. Administrative
  termination is cleanup, not evidence of terminal workflow failure.

Compare categories, source hashes, markers, commands, and ledger counts with the
[model bridge](model-bridges.md), [cancellation](cancellation-results.md), and
[activity](activity-results.md) reports. Histories contain run-specific identifiers;
new history hashes need not equal old ones. Do not rerun the report generators in
record mode to replace frozen evidence with your results.

## Return evidence and objections

Retain `review-output/` and `review-subject/research/results/`, including failed
commands, raw histories, ledgers, and source manifests. Fill the response template
with actual results and objections. Include setup interventions and any assistance.
A public repository/issue link is useful if you consent to public retention; the
invitation makes no assumption about that consent.

The current author smoke test checks only driver planning, provenance rejection,
and the audit stage. It is not external validation. External reproduction and
independent review remain outstanding until a real reviewer supplies a record.
