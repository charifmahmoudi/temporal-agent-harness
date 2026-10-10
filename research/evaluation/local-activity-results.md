# Local-activity identity: completed-history baseline

The [second-mechanism protocol](local-activity-protocol.md) produced twelve live
workflows and same-version replays in
[CI run 38039790691](https://github.com/charifmahmoudi/temporal-agent-harness/actions/runs/38039790691),
driver `622c361e9d919300fa711f3e51addf2b85ff8cc7`.

| Fresh-recording SDK | Local activities | Remote controls |
|---|---|---|
| 1.33.0 | 3 live successes, 3 reported decoding signatures on replay | 3 live/replay successes |
| 1.34.0 | 3 live/replay successes | 3 live/replay successes |

The local failures contain a serialized `TypeError` cause with the reported
str/bool mismatch inside Core's outer `RuntimeError`. Every affected local history
records `identity_expired` at sequence 4 and `identity_finish` afterward. All live
workflow results equal `finished`. Fixed local markers include `activation_index`;
affected markers do not. This agrees with the published mechanism and patch, but
does not directly trace every handle binding or establish silent corruption.

## Audit corrections and provenance

The initial collector looked for `LocalActivity`; the actual marker name is
`core_local_activity`. It therefore recorded zero markers incorrectly. Its
exception classifier also looked for a Python `__cause__` object whose type was
`TypeError`; the bridge retains that cause as serialized native failure data
inside a `RuntimeError` string. Initial local failures were conservatively scored
inconclusive rather than falsely reported as passing.

Both errors are fixed in the runner. The
[raw evidence](local-activity-evidence.json) preserves the original artifact bytes,
including those original counts and verdicts. The
[audited summary](local-activity-summary.json) shows original and revised values
side by side. Recognition of the serialized native cause is an explicit scoring
revision after evidence inspection, not a preregistered implementation success.
The documented str/bool signature was specified before execution.

```bash
python research/scripts/audit_local_activity_evidence.py --check
python research/scripts/test_nexus_evidence.py
```

The audit checks all twelve history hashes, final logical payloads, clean live
task histories, local activity identity/result markers, unique trial identities,
shared executable/source hashes, and equal dependency sets except SDK version.
It checks the native cause signature; a generic decoding RuntimeError alone is
not enough. Python is 3.12.15 and CLI 1.7.0 embeds server 1.31.0. The server archive
was checksum-verified before execution. This is fresh same-version replay only;
no repair of affected legacy-marker histories is claimed.

## Consequence

Ordinary completed-history replay with the documented payload oracle detects this
second development mechanism. An open-workflow continuation is not universally
necessary. Together with the Nexus case, the evidence motivates choosing an
appropriate observation boundary per mechanism; it does not yet demonstrate a
difficult selection problem or a better automatic derivation method.

No new defect, cross-framework generality, prevalence estimate, independent
validation, or scientific novelty is claimed. The corrected runner is being
rechecked in CI; that run is validation of our measurement code, not a new mechanism.
