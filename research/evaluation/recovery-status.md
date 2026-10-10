# Recovery research checkpoint

This page is the current decision record; detailed protocols and raw evidence stay
in their linked files. The objective is an open, reproducible scientific contribution.
Known defects provide development fixtures, not discoveries or blind validation.

**2026-10-10: research-question audit in progress.** The
[audit protocol](question-audit-protocol.md) takes precedence over earlier proposed
next steps. Expansion is paused while we check whether any candidate justifies a
new scientific experiment. Evidence consistency will be checked in GitHub CI.

## Evidence ledger

| Investigation | What is established | What it does not establish |
|---|---|---|
| [#673 reproduction](recovery-investigation.md) and [72-trial pilot](recovery-comparison-results.md) | Known live/replay mismatch; tested heuristic has no advantage over random/regression baselines | General advantage for systematic schedule selection |
| [24-trial Nexus context test](open-recovery-results.md) | Immediate completion masks a defect exposed by a later timer; both cache settings fail on the affected SDK; fixed controls pass | Restart is a necessary cause, or continuation generation is new |
| [12-trial local-activity study](local-activity-results.md) plus 12 corrected-runner checks | Same-version immediate replay exposes the affected decoding signature; remote/fixed controls pass; marker/scorer mistakes are corrected transparently | Silent corruption, recovery of old legacy markers, or universal need for open contexts |
| [48-trial conventional suffix sweep](continuation-results.md) | Ordinary enumeration catches the defect; cached first failures precede replay/eviction; all fixed cells pass | Automatic inference of legal suffixes, a reduction theorem, or a measured advantage |

## Current research judgment

The missing test context is real. Ordinary enumeration catches the Nexus case;
immediate replay catches local-activity identity. A hard selection problem or
advantage over those baselines has not been established.
The inspected [prior work](continuation-prior-work.md) already generates distinguishing
tests and checks behavior after recovery. Our code generates fixtures for a manually
declared grammar; calling that automatic source derivation would overstate it.

Completion, task failures, payload identity, enabled operations, and progress are
different observations. They should be selected from a declared contract. A generic
exception or alarm is not automatically a defect; a completed workflow is not
automatically a sufficient test. SDK state can matter even when application-visible
fields agree. These are useful lessons, not by themselves new theoretical results.

## Gates before proposing a method

- [x] Reproduce externally reported cases with affected/fixed and matched controls.
- [x] Preserve raw evidence and mechanically rederive results.
- [x] Compare state-identification, crash-testing, and persistence-conformance prior work.
- [x] Complete the conventional suffix sweep and identify the first failure's replay state.
- [ ] Establish a concrete deficiency of a baseline equipped with the same grammar/oracle.
- [ ] State a supported language, fault model, observation contract, and technical claim.
- [ ] Obtain independently selected evaluation cases before adapting a method to them.

If ordinary enumeration handles the development cases cheaply, reject an advantage
on those cases. A larger framework is justified only after evidence identifies what
ordinary enumeration, dependency slicing, or model-based state identification cannot
provide adequately. Neither testing more inspected bugs nor publishing more models
substitutes for that comparison.

## Community reproduction and contributions

Start with the result pages and their `--check` commands. The checks require only
Python's standard library and use committed artifacts; live reproduction uses the
pinned CI workflows and upstream SDK source. Every raw bundle includes run/revision
provenance. Do not infer reproduction success from a green collection job.

A useful submitted case should identify the public report/source revision, legal
workflow and environment, reachable boundary, explicit recovery treatment, executable
continuation, expected observations, and affected/fixed control. Include histories
and logs. Label whether its report/fix has already been inspected. New contributions
should preserve negative and inconclusive results and distinguish a new failure
mechanism from another timing variant of an existing one.

No upstream report or invitation has been sent by this project. No changes are merged.
