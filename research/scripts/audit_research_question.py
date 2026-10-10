"""Recheck retained evidence in CI; report facts, not a novelty verdict."""
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
EVALUATION = ROOT / "research/evaluation"
PROTOCOL_COMMIT = "c00ebd11100e341046a7d65d21426d83a8849cf6"
CHECKS = (
    ("summarize_recovery_comparison.py", "--check"),
    ("audit_nexus_evidence.py", "--check"),
    ("audit_nexus_evidence.py", "--check", "--continuations"),
    ("test_nexus_evidence.py",),
    ("audit_local_activity_evidence.py", "--check"),
    ("audit_local_activity_evidence.py", "--check", "--corrected"),
)


def main():
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise SystemExit("This audit is designated for GitHub Actions execution.")
    for name, *args in CHECKS:
        subprocess.run([sys.executable, str(ROOT / "research/scripts" / name), *args],
                       cwd=ROOT, check=True)

    inputs = {}

    def read(name):
        path = EVALUATION / name
        data = path.read_bytes()
        inputs[name] = hashlib.sha256(data).hexdigest()
        return json.loads(data)

    continuation = read("continuation-summary.json")
    nexus = []
    for arm in continuation["arms"]:
        for row in arm["rows"]:
            if row["verdict"] == "confirmed_mechanism":
                states = row["caller_activations_before_first_wake_failure"]
                nexus.append({
                    "arm": arm["arm"], "case": row["case"],
                    "repetition": row["repetition"],
                    "only_live_non_eviction_before_first_failure":
                        bool(states) and all(s == ["false", "false"] for s in states),
                    "wake_failure_markers": row["wake_failure_markers"],
                })

    identity = {}
    for name in ("local-activity-summary.json", "local-activity-corrected-summary.json"):
        data = read(name)
        identity[name] = {
            "run_url": data["run_url"],
            "cells": [{"sdk": arm["sdk"], "local": local,
                       "verdicts": dict(Counter(row["audited_verdict"]
                           for row in arm["rows"] if row["local"] is local))}
                      for arm in data["arms"] for local in (True, False)],
        }
    schedules = read("recovery-comparison-summary.json")
    context = read("open-recovery-summary.json")
    for name in ("continuation-evidence.json", "open-recovery-evidence.json",
                 "local-activity-evidence.json", "local-activity-corrected-evidence.json",
                 "recovery-comparison-evidence.json"):
        inputs[name] = hashlib.sha256((EVALUATION / name).read_bytes()).hexdigest()
    protocol_path = EVALUATION / "question-audit-protocol.md"
    inputs[protocol_path.name] = hashlib.sha256(protocol_path.read_bytes()).hexdigest()
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    report = {
        "schema": 1, "kind": "retrospective_evidence_audit",
        "protocol_commit": PROTOCOL_COMMIT,
        "evidence_cutoff_commit": "72ed3d82bf11871d526043cbee6c0d0ad9b675bc",
        "run_url": f"https://github.com/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{os.environ['GITHUB_RUN_ID']}",
        "run_attempt": os.environ["GITHUB_RUN_ATTEMPT"],
        "checkout_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "pr_head_commit": event.get("pull_request", {}).get("head", {}).get("sha"),
        "checks_passed": [list(check) for check in CHECKS],
        "input_sha256": inputs,
        "context": {"run_url": context["run_url"],
                    "arms": [{"arm": a["arm"], "verdicts": a["verdicts"]} for a in context["arms"]]},
        "continuation": {"run_url": continuation["run_url"],
                         "arms": [{"arm": a["arm"], "verdicts": a["verdicts"]} for a in continuation["arms"]],
                         "confirmed_failure_activation_records": nexus},
        "identity": identity,
        "schedules": {"run_url": schedules["run_url"],
                      "arms": [{"sdk": a["sdk"], "methods": [
                          {k: m[k] for k in ("method", "verdicts", "first_detection_by_seed", "coverage_by_seed")}
                          for m in a["methods"]]} for a in schedules["arms"]]},
        "new_runtime_trials": 0,
        "limitations": ["Previously observed development cases; no blind holdouts.",
                        "Mechanical consistency does not establish novelty or causal sufficiency.",
                        "Same SDK Core lineage; language bindings are not independent engines."],
    }
    out = ROOT / "research/results/question-audit"
    out.mkdir(parents=True, exist_ok=True)
    (out / "audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print("QUESTION_AUDIT_JSON=" + json.dumps(report, separators=(",", ":")))


if __name__ == "__main__":
    main()
