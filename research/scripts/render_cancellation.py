"""Render the frozen cancellation report and verify retained evidence integrity."""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
DIRECTORY = ROOT / "research/evaluation"


def render():
    result = json.loads((DIRECTORY / "cancellation-results.json").read_text())
    packet = result["upstream_packet"]
    for path, key in (
        (ROOT / "research/upstream/caller-cancellation.patch", "patch_sha256"),
        (ROOT / "research/upstream/test_cancel_and_settle.py", "regression_sha256"),
        (DIRECTORY / "cancellation-evidence/upstream-original.xml", "original_junit_sha256"),
        (DIRECTORY / "cancellation-evidence/upstream-patched.xml", "corrected_junit_sha256"),
    ):
        assert hashlib.sha256(path.read_bytes()).hexdigest() == packet[key]
    for name, failures, passes in (
        ("original", packet["original_failures"], packet["original_passes"]),
        ("patched", 0, packet["corrected_passes"]),
    ):
        cases = list(ET.parse(DIRECTORY / f"cancellation-evidence/upstream-{name}.xml").getroot().iter("testcase"))
        assert len(cases) == failures + passes
        assert sum(c.find("failure") is not None for c in cases) == failures
        assert not any(c.find(tag) is not None for c in cases for tag in ("error", "skipped"))
    for artifact in result["artifacts"].values():
        data = (DIRECTORY / artifact["file"]).read_bytes()
        if hashlib.sha256(data).hexdigest() != artifact["sha256"]:
            raise ValueError("Retained artifact differs from its frozen digest")
    with ZipFile(DIRECTORY / result["artifacts"]["model"]["file"]) as archive:
        if json.loads(archive.read("summary.json")) != result["model"]:
            raise ValueError("Model summary differs from retained raw evidence")
        assert hashlib.sha256(archive.read("Cleanup.tla")).hexdigest() == result["model"]["model_sha256"]
        assert hashlib.sha256(archive.read("Approval.tla")).hexdigest() == result["model"]["base_model_sha256"]
        for row in result["model"]["results"]:
            assert row["passed"]
            log = archive.read(row["configuration"] + ".log").decode()
            if row["returncode"] == 12:
                assert "Invariant CallerCancellationRespected is violated" in log
            elif row["returncode"] == 13:
                assert "Temporal property CleanupProgress was violated." in log
                assert "cleanupPending = TRUE" in log
            else:
                assert row["returncode"] == 0
                assert "Model checking completed. No error has been found." in log
    with ZipFile(DIRECTORY / result["artifacts"]["implementation"]["file"]) as archive:
        provenance = json.loads(archive.read("cancellation-corrected/provenance.json"))
        if provenance != result["source_hashes"]:
            raise ValueError("Source provenance differs from raw evidence")
        harness_cases = list(ET.fromstring(archive.read("cancellation-corrected/harness-results.xml")).iter("testcase"))
        assert len(harness_cases) == result["harness_regressions_passed"]
        assert not any(c.find(tag) is not None for c in harness_cases
                       for tag in ("failure", "error", "skipped"))
        for variant, prefix, xml in (
            ("baseline", "cancellation/baseline/", "cancellation-baseline.xml"),
            ("corrected", "cancellation-corrected/research/results/cancellation/corrected/",
             "cancellation-corrected/results.xml"),
        ):
            row = result["variants"][variant]
            cases = list(ET.fromstring(archive.read(xml)).iter("testcase"))
            assert len(cases) == row["tests_passed"]
            assert not any(c.find(tag) is not None for c in cases
                           for tag in ("failure", "error", "skipped"))
            replays = [json.loads(archive.read(p)) for p in archive.namelist()
                       if p.startswith(prefix) and p.endswith("-replay.json")]
            assert len(replays) == row["history_replays"]
            assert all(p["replay_failure"] is None for p in replays)
            for name, digest in row["history_sha256"].items():
                assert hashlib.sha256(archive.read(prefix + name)).hexdigest() == digest
            for mode, expected in row["caller"].items():
                after = json.loads(archive.read(prefix + f"caller-{mode}.json"))["after"]
                events = [e["type"] for e in after["events"]]
                observed = dict(status=after["status"], outcome=after["outcome"],
                                tool_started="tool_start" in events,
                                evaluation_terminals=events.count("auto_approval_evaluation_superseded"))
                assert observed == expected
                assert after["caller_cancel_requested"] and after["second_cancel"]
            assert json.loads(archive.read(prefix + "restart-recovered.json"))["matches_before"] == row["restart_matches_before"]
            assert json.loads(archive.read(prefix + "workflow-cancel.json"))["terminal_status"] == row["workflow_cancel_status"]
    baseline, fixed = (result["variants"][v] for v in ("baseline", "corrected"))
    rows = []
    for mode in baseline["caller"]:
        b, f = baseline["caller"][mode], fixed["caller"][mode]
        rows.append(f"| {mode} | {b['outcome']}; tool started | {f['outcome']}; no tool start | {b['evaluation_terminals']} / {f['evaluation_terminals']} |")
    models = "\n".join(f"| {r['configuration']} | {r['returncode']} | Expected result confirmed |"
                       for r in result["model"]["results"])
    return f"""# Cancellation and recovery: measured findings

[Case study](../../RESEARCH.md) · [Protocol v2](cancellation-protocol.md) · [Model](../models/cancellation/README.md) · [Upstream packet](../upstream/caller-cancellation.md)

## Finding and significance

**The cleanup helper can swallow cancellation of its waiting caller and permit an
approved tool to execute.** Accepted approval remains stable, so the earlier decision
safety properties do not detect this defect. The case motivates a separate invocation
obligation: cancellation received during cleanup, before dispatch, prevents dispatch.

Discovery came from source inspection and targeted asyncio execution, followed by a
supported custom-agent Temporal reproducer. TLA+ subsequently formalizes the missing
obligation and produces an abstract counterexample. This is not a model-led discovery,
a demonstrated deployment incident, or a global workflow-cancellation defect.

![Accepted approval and caller cancellation](../figures/cancellation.svg)

**Figure 6.** Approval is retained in both paths. Propagating caller cancellation changes
the invocation outcome and prevents the concrete tool-start event.

## Baseline versus isolated correction

Both variants received identical barrier-controlled stimuli. The proposed correction
also emits exactly one superseded evaluation terminal before propagating live caller
cancellation. It remains isolated; this study does not apply it to production source.

| Child response to the second cancellation | Baseline | Isolated correction | Evaluation terminals, baseline / corrected |
| --- | --- | --- | --- |
{chr(10).join(rows)}

All four caller executions retain approved status. Each variant passed
**{baseline['tests_passed']} tests**, including seven asyncio controls and sixteen actual
Temporal executions; **{baseline['history_replays']} completed histories per variant**
replayed without command-compatibility failure. Baseline tests characterize the defect;
their passing does not mean the cancellation contract holds.
All **{result['harness_regressions_passed']} harness regressions** also passed against
the isolated correction.

Separately, the standalone patch was checked against the original upstream revision:
three cancellation assertions fail and four controls pass before correction; all seven
pass after applying the patch. The packet retains both JUnit records and patch hashes.

| Hypothesis | Measured outcome in both variants | Interpretation |
| --- | --- | --- |
| H1: cleanup outcomes | Nine approval/denial/close × propagation/error/return cases preserve settlement | Selected safety controls hold |
| H2: delayed cleanup | Three settled/closed prefixes remain waiting; release permits completion | Cleanup termination is a progress assumption; a finite wait is not proof of an infinite hang |
| H3: caller cancellation | Two baseline dispatches; two corrected cancellations | Reproduced defect with a concrete tool-start witness |
| H4: replacement and replay | Waiting-state equality after nonsticky worker replacement; final approved dispatch | Graceful replacement with caching disabled, not crash recovery or production sticky routing |
| H5: workflow cancellation | Public workflow cancellation ends as CANCELED | Distinct from cancellation of the handler task |

## Formal results

| Configuration | TLC exit code | Interpretation |
| --- | --- | --- |
{models}

CurrentCancellation violates CallerCancellationRespected (exit 12). BlockedProgress
violates CleanupProgress (exit 13) when cleanup cannot finish. All other checks return
zero. Named diagnostics are required; setup errors are not credited as findings.
The one-call corrected projection preserves the original safety obligations and the
new cancellation invariant. It is not a universal Python refinement proof.
The refined model remembers whether Consume superseded a running evaluator.
ReadyTaskNotBlocked and PendingCleanupPhase consistency checks ensure that a task
already completed cannot supply a spurious infinite cleanup wait.

## Provenance and retained evidence

The protocol was published at `{result['protocol_commit']}` before the Temporal
experiments. Final evidence is from [run {result['run_id']}]({result['run_url']}) at
`{result['execution_commit']}`. The [machine-readable snapshot](cancellation-results.json)
contains source/model/tool hashes, history hashes, artifact IDs, and observed outcomes.
The exact [implementation archive](cancellation-evidence/implementation.zip) and
[model archive](cancellation-evidence/model.zip) are committed so CI artifact expiry
does not remove the evidence. They retain raw events, full histories, replay results,
JUnit XML, the isolated production diff, configurations, and TLC counterexamples.

`python research/scripts/render_cancellation.py --check` verifies their digests and
the reported outcomes against raw records. The executable reproduction reference is
the [cancellation workflow](../../.github/workflows/cancellation.yml). It prepares an
isolated correction with import/source provenance checks and runs both variants.

## Failed attempts and limits

Runs 37891291257, 37891534941, and 37891860332 failed the worker-replacement query before
recovering usable state. The first also exposed an expected-diagnostic mismatch in the
model runner. Their [protocol amendments](cancellation-protocol.md) explain the eventual
nonsticky procedure. They establish neither recovery correctness nor a recovery defect.
Run 37892043434 passed with a helper-only correction, but review exposed a missing
evaluation terminal. The final patch and assertions close that audit gap.
The earlier model's BlockedProgress witness could also block an already-completed task;
review led to an explicit running-cleanup distinction. The intermediate evidence is
retained at commit `{result['intermediate_evidence']['retained_at_commit']}` and identified
in the snapshot. Only the refined model supports this report's progress interpretation.

The result is a reproducible implementation defect and a useful separation of decision
safety, invocation cancellation, audit completeness, and cleanup-dependent progress.
Deployment frequency, arbitrary-call behavior, external-effect rollback, process crashes,
mixed-version replay, and children that suppress cancellation forever remain unmeasured.
Independent review, external reproduction, and research novelty assessment remain open.
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    path = DIRECTORY / "cancellation-results.md"
    text = render()
    if args.check:
        if path.read_text() != text:
            raise SystemExit("Cancellation report drifted from retained evidence")
    else:
        path.write_text(text)
    print("Cancellation evidence verified; report is current.")


if __name__ == "__main__":
    main()
