"""Controlled schema intervention on a pinned artifact; CI only."""
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

def adapt(row):
    r = copy.deepcopy(row)
    source = r["verdict"]
    oracle = r["fault_benchmark_hidden"]["oracle_verdict"]
    for src, dst in (("duplicate_effects", "duplicate_effects_count"), ("missing_effects", "missing_effects_count")):
        count = source[src]
        if type(count) is not int or count < 0:
            raise ValueError("Invalid source count")
        if dst in oracle and oracle[dst] != count:
            raise ValueError("Conflicting count")
        oracle[dst] = count
    return r

def main():
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise SystemExit("GitHub CI only")
    subject = Path(sys.argv[1]).resolve()
    sys.path.insert(0, str(subject))
    from recoverbench.engine import BenchmarkEngine
    source = subject / "results/rb3c_test_raw.jsonl"
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    assert digest == "1016768449aae019484130b23fda33456861abeb161a5f8dfbeb16e9e5e9f882"
    with source.open() as f:
        rows = [json.loads(line) for line in f if line.strip()]
    original = BenchmarkEngine.evaluate_trajectories_file(str(source))
    converted = [adapt(r) for r in rows]
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp) / "adapted.jsonl"
        path.write_text("".join(json.dumps(r) + "\n" for r in converted))
        adapted = BenchmarkEngine.evaluate_trajectories_file(str(path))
    keep = ("total_pairs", "control_passed", "fault_passed", "crsr_passed", "eor_passed",
            "duplicate_effects_count", "missing_effects_count", "crsr", "eor", "der", "mer")
    report = {
        "run_id": os.environ["GITHUB_RUN_ID"], "input_sha256": digest,
        "original": {k: original[k] for k in keep},
        "adapted": {k: adapted[k] for k in keep},
        "absent_nested_duplicate_count": sum("duplicate_effects_count" not in r["fault_benchmark_hidden"]["oracle_verdict"] for r in rows),
        "absent_nested_missing_count": sum("missing_effects_count" not in r["fault_benchmark_hidden"]["oracle_verdict"] for r in rows),
        "first_duplicate_pair": next(r["pair_id"] for r in rows if r["verdict"]["duplicate_effects"] > 0),
        "first_missing_pair": next(r["pair_id"] for r in rows if r["verdict"]["missing_effects"] > 0),
    }
    conflict = copy.deepcopy(rows[0])
    conflict["fault_benchmark_hidden"]["oracle_verdict"]["duplicate_effects_count"] = conflict["verdict"]["duplicate_effects"] + 1
    missing = copy.deepcopy(rows[0])
    del missing["verdict"]["missing_effects"]
    rejected = []
    for name, row in (("conflicting_count", conflict), ("missing_source_count", missing)):
        try:
            adapt(row)
        except (KeyError, ValueError):
            rejected.append(name)
    report["rejected_controls"] = rejected
    report["matches_prediction"] = (
        original["duplicate_effects_count"] == 0 and original["missing_effects_count"] == 0
        and adapted["duplicate_effects_count"] == 1444 and adapted["missing_effects_count"] == 284
        and all(original[k] == adapted[k] for k in ("total_pairs", "control_passed", "fault_passed", "crsr_passed", "eor_passed", "crsr", "eor"))
        and len(rejected) == 2)
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    (out / "schema-audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    assert report["matches_prediction"]

if __name__ == "__main__":
    main()
