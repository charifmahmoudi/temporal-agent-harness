# Consequence-led incident discovery

Status: exploratory round in progress. Prior contribution proposals remain rejected.
This protocol precedes incident coding and any new executable probe. Orientation has
already read the previous 43-record inventory and searched Temporal server issues for
`"data loss"`; those observations are not prospective or held out.

## Selection and evidence

Study 10–15 public incident reports in depth across Temporal, DBOS, and Restate.
Start with consequential reports from the earlier inventory, then search server/SDK
issues for `stuck`, `duplicate`, `upgrade`, and `"data loss"`. These are purposive
consequence searches, not random sampling or a prevalence estimate. Retain search
results and exclusions. Prefer concrete loss of progress, inconsistent state, failed
upgrades, or manual repair over feature requests; do not promote claimed severity to
verified impact. Collapse shared root causes. All selected cases are development data.

For every case read the report, discussion, and available resolution/implementation.
Record reported consequence, operator decision, established answer, remaining unknown,
source links, evidence strength, and whether external-effect safety was actually
measured. A closed issue is not proof of a fix. Missing implementation evidence stays
explicit rather than being inferred from issue state.

## Four activities and decision gate

1. Deep-read 10–15 selected reports, including corrections and adequate existing answers.
2. Extract the operator's unanswered decision; separate absent measurement from an
   unexplained mechanism and from an established theoretical limitation.
3. Select at most one question with competing explanations. Publish a separate probe
   protocol before its implementation/execution. Define observations that weaken each
   explanation; conventional documentation and tools receive equal information.
4. Expand only if the result justifies a specific claim. Freeze the claim/evaluation
   before independent validation; do not relabel inspected cases as held out.

All executable probes and checks run in GitHub CI. Local work is reading/editing and
Git operations only. Retain setup errors, raw evidence, versions, and failed predictions.
If no incident supports a discriminating experiment, document that decision instead of
manufacturing another known-contract confirmation. This is a permitted outcome, not a
claim that no scientific opportunity exists. No upstream messages or human study are
part of this round.
