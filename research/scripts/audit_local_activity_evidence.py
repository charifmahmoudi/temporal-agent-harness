"""Audit the preserved identity study, retaining original and revised verdicts."""
import argparse
import base64
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import zipfile

from identity_scoring import decoding_mechanism

ROOT = Path(__file__).resolve().parents[1]


def payload(value):
    return json.loads(base64.b64decode(value["data"]))


def audit(bundle):
    raw = base64.b64decode(bundle["archive_zip_base64"], validate=True)
    assert hashlib.sha256(raw).hexdigest() == bundle["archive_sha256"]
    archive = zipfile.ZipFile(io.BytesIO(raw))
    outputs, servers, sources, dependencies = [], set(), set(), []
    for release in ("1.33", "1.34"):
        report = json.loads(archive.read(f"{release}/report.json"))
        assert report["sdk"] == release + ".0"
        assert report["infrastructure_error"] is None
        assert len(report["rows"]) == 6
        assert "Server 1.31.0" in report["cli_version"]
        servers.add(report["server_sha256"])
        sources.add(report["runner_sha256"])
        dependencies.append(set(archive.read(f"dependencies-{release}.txt").decode().splitlines())
                            - {"temporalio==" + release + ".0"})
        seen, rows = set(), []
        for row in report["rows"]:
            local, rep = row["local"], row["repetition"]
            assert isinstance(local, bool) and rep in (1, 2, 3)
            assert (local, rep) not in seen
            seen.add((local, rep))
            path = f"{release}/r{rep}-{'local' if local else 'remote'}/history.json"
            data = archive.read(path)
            assert hashlib.sha256(data).hexdigest() == row["history_sha256"]
            events = json.loads(data)["events"]
            completed = [e["workflowExecutionCompletedEventAttributes"] for e in events
                         if "workflowExecutionCompletedEventAttributes" in e]
            assert len(completed) == 1
            assert payload(completed[0]["result"]["payloads"][0]) == row["live_result"] == "finished"
            assert not any("workflowTaskFailedEventAttributes" in e or "workflowTaskTimedOutEventAttributes" in e for e in events)
            markers = []
            for event in events:
                marker = event.get("markerRecordedEventAttributes", {})
                if marker.get("markerName") != "core_local_activity":
                    continue
                details = marker["details"]
                markers.append({"event_id": int(event["eventId"]),
                    "data": payload(details["data"]["payloads"][0]),
                    "result": payload(details["result"]["payloads"][0])})
            if local:
                works = [m for m in markers if m["data"]["activity_type"] == "identity_work"]
                assert len(works) == 3 and {m["result"] for m in works} == {"0", "1", "2"}
                assert sorted(m["data"]["seq"] for m in works) == [1, 2, 3]
                ends = [m for m in markers if m["data"]["activity_type"] == "identity_finish"]
                assert len(ends) == 1 and ends[0]["result"] == "finished"
                expired = [m for m in markers if m["data"]["activity_type"] == "identity_expired"]
                assert all(m["result"] is False for m in expired)
                assert all(("activation_index" in m["data"]) == (release == "1.34") for m in markers)
            else:
                assert not markers
                assert sum("activityTaskScheduledEventAttributes" in e for e in events) == row["remote_schedule_count"]
            original = row["verdict"]
            revised = "reported_decoding_mechanism" if decoding_mechanism(row["replay_exception"]) else original
            if revised == "reported_decoding_mechanism":
                assert local and len(markers) > 4
                assert any(m["data"]["seq"] == 4 and m["data"]["activity_type"] == "identity_expired" for m in markers)
            if revised == "compatible":
                assert not row["replay_exception"]
            rows.append({"local": local, "repetition": rep, "original_verdict": original,
                "audited_verdict": revised, "original_marker_count": row["local_marker_count"],
                "audited_marker_count": len(markers), "markers": markers})
        outputs.append({"sdk": report["sdk"], "verdicts": dict(Counter(r["audited_verdict"] for r in rows)), "rows": rows})
    assert len(servers) == len(sources) == 1
    assert dependencies[0] == dependencies[1]
    return {"schema": 1, "run_url": bundle["run_url"], "arms": outputs,
        "server_sha256": next(iter(servers)), "runner_sha256": next(iter(sources)),
        "shared_dependencies": sorted(dependencies[0]),
        "scoring_revision": "Recognize serialized Core TypeError cause and core_local_activity marker name; original artifact unchanged"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    report = audit(json.loads((ROOT / "evaluation/local-activity-evidence.json").read_text()))
    target = ROOT / "evaluation/local-activity-summary.json"
    encoded = json.dumps(report, indent=2) + "\n"
    if args.check:
        assert target.read_text() == encoded
    else:
        target.write_text(encoded)
    print("12 local/remote histories, payloads, marker metadata, and dependencies verified; original scoring preserved.")
