"""Re-derive incident probe observations from retained ZIPs; run in CI only."""
import base64
import copy
import hashlib
import io
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "research/discovery/incidents"


def decode(archive, name):
    return json.loads(archive.read(name))


def evidence_cell(z, backend, suffix, mutation):
    prefix = f"{backend}/{suffix}-{mutation}/"
    return {"backend": backend, "suffix": suffix, "mutation": mutation,
            "pre": decode(z, prefix + "pre.json"),
            "operator": decode(z, prefix + "after-operator.json"),
            "post": decode(z, prefix + "post.json"),
            "first": [json.loads(s) for s in z.read(prefix + "first-trace.jsonl").decode().splitlines()],
            "recover": [json.loads(s) for s in z.read(prefix + "recover-trace.jsonl").decode().splitlines()]}


def assess(c):
    pre, post = c["pre"], c["post"]
    assert pre["status"]["workflow_id"] == post["status"]["workflow_id"] == "W"
    assert pre["status"]["status"] == "PENDING"
    assert pre["schedule"] is not None
    assert [e["value"] for e in c["first"] if e["event"] == "branch"] == ["A"]
    assert [e["value"] for e in c["first"] if e["event"] == "marker_body"] == ["A"]
    assert c["first"][-1]["event"] == "crash_after_marker"
    assert not any(e["event"] == "unexpected_schedule_fire" for e in c["first"] + c["recover"])
    assert len(pre["raw_operations"]) == 1
    marker = pre["raw_operations"][0]
    assert marker["workflow_uuid"] == "W" and marker["function_id"] == 2
    assert marker["function_name"].endswith("mark") and marker["error"] is None
    assert len(pre["steps"]) == 1 and pre["steps"][0]["output"] == "A"
    if c["mutation"] == "delete":
        assert c["operator"]["schedule"] is None
    else:
        assert c["operator"]["schedule"]["schedule_id"] == pre["schedule"]["schedule_id"]
    branches = [e["value"] for e in c["recover"] if e["event"] == "branch"]
    rows = post["raw_operations"]
    old_markers = [r for r in rows if r["function_id"] == 2]
    assert len(old_markers) == 1
    for field in ("function_name", "output", "error"):
        assert old_markers[0][field] == marker[field]
    created = [r for r in rows if r["function_id"] == 1 and r["function_name"] == "DBOS.createSchedule" and r["error"] is None]
    recreated = (c["operator"]["schedule"] is None and post["schedule"] is not None)
    if recreated:
        assert len(created) == 1
        assert post["schedule"]["schedule_id"] != pre["schedule"]["schedule_id"]
    status = post["status"]["status"]
    if status == "SUCCESS":
        assert "result" in post and post["status"]["output"] == post["result"]
    predicted = (not post["bounded_timeout"] and
                 ((c["mutation"] == "retain" and status == "SUCCESS" and post.get("result") == "A" and branches == ["A"] and not recreated)
                  or (c["mutation"] == "delete" and recreated and branches == ["B"] and
                      ((c["suffix"] == "same" and status == "SUCCESS" and post.get("result") == "A")
                       or (c["suffix"] == "different" and status == "ERROR" and post.get("exception", {}).get("type") == "DBOSUnexpectedStepError")))))
    return {"backend": c["backend"], "suffix": c["suffix"], "mutation": c["mutation"],
            "status": status, "result": post.get("result"), "exception": post.get("exception"),
            "recovery_branches": branches, "schedule_recreated": recreated,
            "new_success_checkpoint": bool(created), "bounded_timeout": post["bounded_timeout"],
            "matches_prediction": predicted}


def main():
    manifest = json.loads((BASE / "artifacts.json").read_text())
    results, cells, initial = [], [], 0
    for artifact in manifest:
        raw = base64.b64decode((BASE / artifact["path"]).read_bytes())
        assert hashlib.sha256(raw).hexdigest() == artifact["sha256"]
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            backend = artifact["backend"]
            collection = decode(z, backend + "/collection.json")
            assert len(collection) == 4
            assert {(c["suffix"], c["mutation"]) for c in collection} == {(s, m) for s in ("same", "different") for m in ("retain", "delete")}
            for c in collection:
                if artifact["attempt"] == "initial":
                    assert c["collection"] == "inconclusive"
                    assert c["processes"] == {"first": 17, "recover": 1}
                    initial += 1
                    continue
                assert c["collection"] == "complete" and c["processes"] == {"first": 17, "recover": 0}
                cell = evidence_cell(z, backend, c["suffix"], c["mutation"])
                cells.append(cell)
                results.append(assess(cell))
    assert len(cells) == 8 and initial == 8
    # Evidence-integrity controls: reject invalid starting state, wrong original
    # branch, and an operator intervention contradicted by its retained snapshot.
    for mutation in ("status", "branch", "operator"):
        fake = copy.deepcopy(next(c for c in cells if c["mutation"] == "delete"))
        if mutation == "status":
            fake["pre"]["status"]["status"] = "SUCCESS"
        elif mutation == "branch":
            next(e for e in fake["first"] if e["event"] == "branch")["value"] = "B"
        else:
            fake["operator"]["schedule"] = fake["pre"]["schedule"]
        try:
            assess(fake)
        except AssertionError:
            pass
        else:
            raise AssertionError("audit accepted contradictory " + mutation)
    report = {"initial_inconclusive": initial, "corrected_cells": results, "negative_controls": 3}
    out = ROOT / "research/results/incident-audit"
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
