# Conventional continuation baseline: completed comparison

## Result

All 48 frozen cells executed and yielded usable evidence. Ordinary enumeration
of the declared suffix grammar exposes the known Nexus defect.

| Suffix after successful result | Affected / cached | Affected / cold | Fixed / cached | Fixed / cold |
|---|---|---|---|---|
| Return | 3 passed | 3 passed | 3 passed | 3 passed |
| Synchronous state read/assert | 3 passed | 3 passed | 3 passed | 3 passed |
| Zero-duration SDK timer | 3 confirmed failures | 3 confirmed failures | 3 passed | 3 passed |
| One-second SDK timer | 3 confirmed failures | 3 confirmed failures | 3 passed | 3 passed |

No cell is inconclusive. Both timers record a legal timer start/fire and expose
TMPRL1100 after the Nexus result. A host delay is unnecessary. The fixed revision
passes all 24 cells, including completed-history replay and logical payload checks.

**The cached first failure does not require reconstruction.** In all six affected
cached timer trials, the caller has only `replay=false, eviction=false` activations
before the first wake-failure marker. The marker itself reports `replay=false`.
Cold runs have earlier reconstruction activations, but their first failure markers
also report `replay=false`. This distinguishes an earlier recovery path from the
mode of the activation that reports failure. We filter by the caller's original
run ID; backing-workflow and subsequent retry/eviction observations are excluded
from the first-failure conclusion.

This narrows the upstream recovery account for our adapted fixture. It does not
refute that queries/restarts can expose the same defect in another workflow. The
[initial observer-free experiment](open-recovery-results.md) confirms detection
without diagnostic instrumentation; the detailed activation claim uses logs from
this instrumented run. Timing/performance equivalence is not asserted.

## Provenance and executable audit

[CI run 38039466357](https://github.com/charifmahmoudi/temporal-agent-harness/actions/runs/38039466357),
driver `32475aaf057754467626774812c4c9de44de99ec`; preceding remote
protocol commit `e786de3fc302d5a2aebdb1d29740dab50c0575b8`.
See the unchanged [frozen protocol](continuation-protocol.md).

The [raw bundle](continuation-evidence.json) preserves both original artifact ZIPs,
complete histories/logs, generated source/diagnostic patches, source hashes,
dependency locks, and server information. The
[derived summary](continuation-summary.json) includes every trial, the caller's
activation states, and its states before the first recorded wake failure.

```bash
python research/scripts/audit_nexus_evidence.py --check --continuations
python research/scripts/test_nexus_evidence.py
```

All history and artifact hashes, logical result payloads, failure ordering,
live/offline phases, case identities, fixture hashes, and shared dependencies
are checked. Both arms share the same lockfile; its hash also equals the initial
24-cell experiment's lockfile hash. Server 1.31.0 and checksum-pinned CLI 1.7.0
are unchanged. Original collected classifications agree with the stricter audit.

## Scientific decision

The baseline reaches a triggering suffix at the third entry (`return`, `state`,
`timer0`) in its fixed enumeration, in every affected cache/repetition group.
This is a descriptive budget for one known defect. No random comparison,
instrumentation-cost saving, independent holdout, or asymptotic reduction is measured.

The development case requires an adequate continuation, but not a new selection
algorithm. The [local-activity mechanism](local-activity-results.md) is also caught
by a straightforward completed-history baseline. Thus these cases **do not
establish a limitation of well-equipped conventional testing**. They support
maintaining a reproducible corpus and appropriate semantic oracles; they do not
support a claim of superior automatic continuation derivation.

Source/SDK abstraction and selection at larger bounds remain possible questions,
but evidence of a difficult baseline limitation must precede a method proposal.
The [research checkpoint](recovery-status.md) records that gate. Distinguishing
continuations are already established [prior work](continuation-prior-work.md).
