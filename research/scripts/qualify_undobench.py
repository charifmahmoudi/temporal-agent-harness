"""Qualify a pinned public artifact; execute only in GitHub CI."""
import collections
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

EXPECTED = "1016768449aae019484130b23fda33456861abeb161a5f8dfbeb16e9e5e9f882"


def aggregate(rows):
    counts = collections.Counter()
    methods = collections.defaultdict(collections.Counter)
    samples = collections.defaultdict(list)
    ids = set()
    for row in rows:
        v = row["verdict"]
        pid = row["pair_id"]
        c, f = bool(v["ctrl_success"]), bool(v["fault_success"])
        dup, miss = v["duplicate_effects"] > 0, v["missing_effects"] > 0
        unsafe = v["recovery_outcome"] == "UNSAFE_RETRY"
        wire = row.get("fault_benchmark_hidden", {}).get("effect_log", [])
        mutations = sum(bool(e.get("committed_externally")) for e in wire)
        facts = {
            "pairs": True, "control_success": c, "fault_success": f,
            "conditional_success": c and f,
            "fault_success_without_control": f and not c,
            "duplicate": dup, "missing": miss, "unsafe_label": unsafe,
            "unsafe_label_without_duplicate": unsafe and not dup,
            "duplicate_without_unsafe_label": dup and not unsafe,
            "conditional_eor_from_flags_and_wire": c and f and not dup and not miss and mutations > 0,
            "successful_fault_without_wire_commit": f and mutations == 0,
            "stored_commit_count_differs_from_wire": v.get("committed_mutations") != mutations,
            "repeated_pair_id": pid in ids,
        }
        ids.add(pid)
        for key, value in facts.items():
            counts[key] += int(value)
            methods[v["recovery_code"]][key] += int(value)
            if value and key in ("unsafe_label_without_duplicate", "duplicate_without_unsafe_label",
                                 "fault_success_without_control", "stored_commit_count_differs_from_wire"):
                if len(samples[key]) < 3:
                    samples[key].append({
                        "pair_id": pid, "task_id": v.get("task_id"),
                        "outcome": v["recovery_outcome"], "duplicates": v["duplicate_effects"],
                        "missing": v["missing_effects"], "stored_commits": v.get("committed_mutations"),
                        "wire_commits": mutations,
                    })
    return {"counts": dict(counts), "by_method": {k: dict(v) for k, v in sorted(methods.items())},
            "samples": dict(samples), "unique_pairs": len(ids)}


def fixture_checks():
    def row(pid, c, f, dup, miss, outcome):
        return {"pair_id": pid, "verdict": {"ctrl_success": c, "fault_success": f,
            "duplicate_effects": dup, "missing_effects": miss, "recovery_outcome": outcome,
            "recovery_code": "fixture", "committed_mutations": 1},
            "fault_benchmark_hidden": {"effect_log": [{"committed_externally": True}]}}
    rows = [row("a", False, True, 0, 0, "SUCCESS"),
            row("b", True, False, 1, 0, "UNSAFE_RETRY"),
            row("c", True, False, 0, 1, "MISSING_EFFECT")]
    c = aggregate(rows)["counts"]
    assert c["fault_success"] == 1 and c["conditional_success"] == 0
    assert c["duplicate"] == 1 and c["missing"] == 1
    assert c["unsafe_label"] == 1 and c["unsafe_label_without_duplicate"] == 0
    return {"conditional_numerator": "passed", "duplicate_vs_missing": "passed"}


def main():
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise SystemExit("Run this study in GitHub CI only.")
    subject, output = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    output.mkdir(parents=True, exist_ok=True)
    report = {"fixture_checks": fixture_checks(), "run_id": os.environ.get("GITHUB_RUN_ID"),
              "checkout": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
              "subject_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=subject, text=True).strip()}
    commands = {
        "smoke": ["undobench", "smoke"],
        "evaluate": ["undobench", "evaluate", "results/rb3c_test_raw.jsonl"],
        "reproduce_eor": [sys.executable, "scripts/reproduce_eor.py", "--json"],
        "freeze_integrity": [sys.executable, "-m", "pytest", "-q", "tests/test_freeze_integrity.py"],
    }
    report["commands"] = {}
    for name, command in commands.items():
        with (output / (name + ".log")).open("w") as log:
            try:
                result = subprocess.run(command, cwd=subject, stdout=log, stderr=subprocess.STDOUT, timeout=180)
                code = result.returncode
            except subprocess.TimeoutExpired:
                code = 124
                log.write("\nBounded observer timeout.\n")
        report["commands"][name] = {"argv": command, "exit_code": code}
    dataset = subject / "results/rb3c_test_raw.jsonl"
    digest = hashlib.sha256(dataset.read_bytes()).hexdigest()
    report["dataset_sha256"] = digest
    report["hash_matches"] = digest == EXPECTED
    if report["hash_matches"]:
        with dataset.open() as f:
            report["independent_aggregation"] = aggregate(json.loads(line) for line in f if line.strip())
    (output / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["hash_matches"] and all(v["exit_code"] == 0 for v in report["commands"].values()) else 1


if __name__ == "__main__":
    sys.exit(main())
