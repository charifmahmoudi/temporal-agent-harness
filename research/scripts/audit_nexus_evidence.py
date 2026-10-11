"""Audit ZIP-backed Nexus evidence without extracting or rewriting raw artifacts."""
import argparse
import base64
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile

from run_nexus_context import CASES, classify
from prepare_nexus_context import REVISIONS, SOURCE_HASH

ROOT = Path(__file__).resolve().parents[1]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def attributes(event):
    return next(iter(event["attributes"].values()))


def audit(bundle, cases=CASES):
    locks, fixtures, versions = set(), set(), set()
    reports = []
    for arm in bundle["arms"]:
        raw = base64.b64decode(arm["archive_zip_base64"], validate=True)
        assert sha(raw) == arm["archive_sha256"], "Archive hash mismatch"
        archive = zipfile.ZipFile(io.BytesIO(raw))
        provenance = json.loads(archive.read("fixture/provenance.json"))
        revision = provenance["sdk_revision"]
        assert revision in REVISIONS
        assert provenance["upstream_sha256"] == SOURCE_HASH
        locks.add(sha(archive.read("fixture/Cargo.lock")))
        if "generated_sha256" in provenance:
            generated = archive.read("fixture/fixture.rs")
            assert sha(generated) == provenance["generated_sha256"]
            fixtures.add(sha(generated))
        else:
            generated = provenance["generated_hashes"]
            for path, expected in generated.items():
                assert sha(archive.read("fixture/" + Path(path).name)) == expected
        rows = json.loads(archive.read("runs/summary.json"))
        assert len(rows) == len(cases) * 3
        seen, output = set(), []
        for row in rows:
            case, repetition = row["case"], row["repetition"]
            assert case in cases and repetition in (1, 2, 3)
            assert (case, repetition) not in seen
            seen.add((case, repetition))
            assert row["sdk_revision"] == revision
            prefix = f"runs/r{repetition}/{case}/"
            history_bytes = archive.read(prefix + case + ".json")
            assert sha(history_bytes) == row["history_sha256"]
            history = json.loads(history_bytes)
            log = archive.read(prefix + "test.log").decode()
            verdict = classify(history, log, row["returncode"], case)
            assert verdict["verdict"] == row["verdict"], "Stored scoring disagrees with raw evidence"
            events = history["events"]
            ids = [int(e["event_id"]) for e in events]
            assert ids == sorted(set(ids))
            completed = [e for e in events if e["event_type"] == 2]
            nexus = [e for e in events if e["event_type"] == 50]
            assert len(nexus) == 1
            result = json.loads(base64.b64decode(attributes(nexus[0])["result"]["data"]))
            assert result == "completed async"
            if verdict["verdict"] == "passed":
                assert len(completed) == 1
                payload = attributes(completed[0])["result"]["payloads"][0]
                returned = json.loads(base64.b64decode(payload["data"]))
                nested = returned["status"]["Completed"]
                assert json.loads(base64.b64decode(nested["data"])) == result
            failures = [e for e in events if e["event_type"] == 9]
            matching = [e for e in failures if "TMPRL1100" in json.dumps(e)
                        and "non-SDK source" in json.dumps(e)]
            if verdict["verdict"] == "confirmed_mechanism":
                assert matching and min(e["event_id"] for e in matching) > nexus[0]["event_id"]
                assert f"RECOVERY_PHASE {case} live=alarm" in log
                assert f"RECOVERY_PHASE {case} offline=start" not in log
            version = json.loads(archive.read(prefix + "server-version.txt"))["serverVersion"]
            versions.add(version)
            caller_run = attributes(events[0])["original_execution_run_id"]
            failure_markers = [replay for run, replay in re.findall(
                r"CONTINUATION_WAKE_FAILURE run=(\S+) replay=(true|false)", log) if run == caller_run]
            activations = [[replay, eviction] for run, replay, eviction in re.findall(
                r"CONTINUATION_HOST run=(\S+) replay=(true|false) eviction=(true|false)", log) if run == caller_run]
            marker = f"CONTINUATION_WAKE_FAILURE run={caller_run} replay="
            prefix_log = log.split(marker, 1)[0] if marker in log else ""
            before_failure = [[replay, eviction] for run, replay, eviction in re.findall(
                r"CONTINUATION_HOST run=(\S+) replay=(true|false) eviction=(true|false)", prefix_log) if run == caller_run]
            output.append({"case": case, "repetition": repetition, **verdict,
                "nexus_completed_event": nexus[0]["event_id"],
                "timer_fired_events": [e["event_id"] for e in events if e["event_type"] == 18],
                "first_failure_event": min((e["event_id"] for e in matching), default=None),
                "caller_run_id": caller_run, "caller_activation_states": activations,
                "caller_activations_before_first_wake_failure": before_failure,
                "wake_failure_markers": failure_markers})
        reports.append({"arm": arm["arm"], "sdk_revision": revision,
            "verdicts": dict(Counter(r["verdict"] for r in output)), "rows": output})
    assert len(reports) == 2
    assert len(locks) == len(versions) == 1
    if fixtures:
        assert len(fixtures) == 1
    return {"schema": 1, "run_url": bundle["run_url"], "shared_lock_sha256": next(iter(locks)),
        "server_version": next(iter(versions)), "arms": reports}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--continuations", action="store_true")
    args = parser.parse_args()
    name = "continuation" if args.continuations else "open-recovery"
    cases = CASES
    if args.continuations:
        from prepare_nexus_continuations import SUFFIXES
        cases = [f"nexus_continuation_{s}_{c}" for s in SUFFIXES for c in ("cached", "cold")]
    bundle = json.loads((ROOT / f"evaluation/{name}-evidence.json").read_text())
    report = audit(bundle, cases)
    target = ROOT / f"evaluation/{name}-summary.json"
    encoded = json.dumps(report, indent=2) + "\n"
    if args.check:
        assert target.read_text() == encoded, "Derived summary drift"
    else:
        target.write_text(encoded)
    print(f"{sum(len(a['rows']) for a in report['arms'])} histories, payloads, hashes, logs, and shared dependencies verified.")


if __name__ == "__main__":
    main()
