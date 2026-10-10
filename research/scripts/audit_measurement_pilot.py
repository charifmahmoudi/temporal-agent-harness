"""Bounded evaluator audit. All numerical execution is restricted to GitHub CI."""
import collections
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def identity_report(rows, keys):
    counts = collections.Counter(tuple(r[k] for k in keys) for r in rows)
    return {"rows": len(rows), "unique": len(counts),
            "duplicate_identities": [list(k) for k, n in counts.items() if n > 1]}


def perturb(rows, field, scorer):
    variants = {"missing": copy.deepcopy(rows), "null": copy.deepcopy(rows),
                "duplicate": rows + [copy.deepcopy(rows[0])], "empty": []}
    del variants["missing"][0][field]
    variants["null"][0][field] = None
    results = {}
    for name, changed in variants.items():
        try:
            results[name] = {"status": "returned", "output": scorer(changed)}
        except Exception as exc:
            results[name] = {"status": "rejected", "exception": type(exc).__name__, "message": str(exc)}
    return results


def command(argv, cwd, out, name):
    with (out / (name + ".log")).open("w") as log:
        try:
            proc = subprocess.run(argv, cwd=cwd, stdout=log, stderr=subprocess.STDOUT, timeout=180)
            return {"argv": argv, "exit_code": proc.returncode}
        except subprocess.TimeoutExpired:
            return {"argv": argv, "exit_code": 124, "status": "inconclusive_timeout"}


def provenance(root, files):
    records = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(files))}
    return {"files": records, "manifest_sha256": hashlib.sha256(json.dumps(records, sort_keys=True).encode()).hexdigest()}


def audit_arb(root, out):
    mod = load_module("arb_summary", root / "examples/summarize_results.py")
    path = root / "results/arb_frontier_results.json"
    rows = json.loads(path.read_text())["results"]
    keys = ("model", "failure_probability", "task_id", "trial")
    official = mod.build_summary(rows)
    (out / "official-summary.md").write_text(official)
    grouped = collections.defaultdict(list)
    for row in rows:
        grouped[(row["model"], row["failure_probability"])].append(row)
    comparisons = []
    for (model, probability), group in sorted(grouped.items()):
        n = len(group)
        counts = {k: sum(int(r[k]) for r in group) for k in ("success", "recovered")}
        comparisons.append({"model": model, "p": probability, "n": n, "counts": counts,
                            "independent": {k: v / n for k, v in counts.items()},
                            "official": {k: mod._metric_value(rows, model, probability, k) for k in counts}})
    table_agrees = all(c["independent"] == c["official"] for c in comparisons)
    completion_disagreements = []
    for row in rows:
        actual, expected = row["answer"], row["expected_answer"]
        if isinstance(expected, (int, float)):
            correct = isinstance(actual, (int, float)) and abs(actual - expected) < 1e-9
        else:
            correct = actual == expected
        if correct != row["success"]:
            completion_disagreements.append({k: row[k] for k in keys})
    def scored(changed):
        result = mod.build_summary(changed)
        # Retain the actual report, including any unsupported narrative.
        return {"report": result, "input_rows": len(changed)}
    claims = [c for c in comparisons if c["p"] in (0.05, 0.20)
              and (c["model"] == "arb-resilient" or c["model"].startswith("llm-"))]
    return {"identity": identity_report(rows, keys), "comparisons": comparisons,
            "table_agrees": table_agrees,
            "committed_summary_byte_identical": official == (root / "results/summary.md").read_text(),
            "completion_disagreements": completion_disagreements,
            "headline_evidence": claims,
            "perturbations": perturb(rows, "success", scored),
            "provenance": provenance(root, [path, root / "results/summary.md", root / "examples/summarize_results.py"])}


def audit_aerb(root, out):
    mod = load_module("aerb_metrics", root / "src/eval/metrics.py")
    verifier = load_module("aerb_verifiers", root / "src/eval/verifiers.py")
    path = root / "results/phase2_pilot/transcripts.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    keys = ("model", "toolset", "condition", "task_id")
    official = mod.compute_metrics(rows)
    (out / "official-metrics.json").write_text(json.dumps(official, indent=2))
    baseline = {(r["model"], r["toolset"], r["task_id"]) for r in rows
                if r["condition"] == "baseline" and r["success"] is True}
    groups = collections.defaultdict(list)
    for row in rows:
        groups[(row["model"], row["toolset"], row["condition"])].append(row)
    comparisons = []
    for key, group in sorted(groups.items()):
        population = {"success_rate": group,
                      "recovery_rate": [r for r in group if r["primary_fired"] > 0],
                      "compound_survival": [r for r in group if r["primary_fired"] > 0 and r["compound_fired"] > 0],
                      "recovery_rate_conditional": [r for r in group if r["primary_fired"] > 0
                          and (r["model"], r["toolset"], r["task_id"]) in baseline]}
        wanted = {name: round(sum(r["success"] is True for r in pop) / len(pop), 3) if pop else None
                  for name, pop in population.items()}
        name = " | ".join(key)
        comparisons.append({"group": name, "denominators": {k: len(v) for k, v in population.items()},
                            "independent": wanted, "official": {k: official[name][k] for k in wanted},
                            "denominators_agree": (official[name]["n"] == len(group)
                                and official[name]["n_primary_fired"] == len(population["recovery_rate"])
                                and official[name]["n_compound_fired"] == len(population["compound_survival"])
                                and official[name]["n_conditional"] == len(population["recovery_rate_conditional"]))})
    cfgpath = root / "results/phase2_pilot/config.json"
    config = json.loads(cfgpath.read_text())
    tasks = {}
    selected = []
    taskfiles = [root / p for p in config["tasks_files"]]
    for taskfile in taskfiles:
        entries = json.loads(taskfile.read_text())
        tasks.update({t["id"]: t for t in entries})
        selected.extend(entries[:config["task_limit"]])
    disagreements = [{k: r[k] for k in keys} for r in rows if verifier.verify(tasks[r["task_id"]]["verifier"], r) != r["success"]]
    # Independent config expansion; do not import the live model runner.
    grid = config["grid"]
    conditions = ["baseline"] if grid.get("include_baseline", True) else []
    for ftype in grid["failure_types"]:
        for point in grid["injection_points"]:
            for recovery in grid["recoverability"]:
                for compound in grid["compound"]:
                    if compound and (recovery != "transient" or point != "first"):
                        continue
                    name = f"{ftype}_{point}_{recovery}"
                    if compound:
                        name += "_cmp-" + compound["type"]
                    conditions.append(name)
    expected = {(m.get("backend", "ollama") + ":" + m["model"], t["toolset"], c, t["id"])
                for m in config["models"] for t in selected for c in conditions}
    observed = {tuple(r[k] for k in keys) for r in rows}
    def scored(changed):
        table = mod.compute_metrics(changed)
        return {k: {n: v[n] for n in ("n", "success_rate", "recovery_rate", "n_primary_fired")}
                for k, v in table.items()}
    return {"identity": identity_report(rows, keys), "comparisons": comparisons,
            "table_agrees": all(c["independent"] == c["official"] and c["denominators_agree"] for c in comparisons),
            "verifier_disagreements": disagreements,
            "coverage": {"expected": len(expected), "observed": len(observed), "missing": len(expected-observed),
                         "unexpected": len(observed-expected), "missing_examples": [list(k) for k in sorted(expected-observed)[:5]]},
            "perturbations": perturb(rows, "success", scored),
            "provenance": provenance(root, [path, cfgpath, root / "src/eval/metrics.py", root / "src/eval/verifiers.py", *taskfiles])}


def audit_sabot(root, out):
    harness = root / "harness"
    sys.path.insert(0, str(harness))
    mod = load_module("sabot_by_operator", harness / "scripts/score_by_operator.py")
    wave = load_module("sabot_wave2_score", harness / "scripts/score_wave2.py")
    path = harness / "runs/wave2/wave2-rows.json"
    rows = json.loads(path.read_text())
    keys = ("framework", "config", "task", "operator", "seed")
    independent = {"O"+str(i): [0]*7 for i in range(1,7)}
    exclusions = collections.Counter()
    for r in rows:
        if r["excluded"] is not None:
            exclusions[r["excluded"]] += 1
            continue
        if r["framework"] == "autogen" and r["config"] == "guardrail":
            exclusions["not_reviewer_bearing"] += 1
            continue
        vals = [1, int(r["recovered"] is True), int(r["union"] is True), int(r["reacted"] is True),
                int(r["union"] is True and r["recovered"] is False),
                int(r["recovered"] is True and r["union"] is False), int(r["flags_anchored"] is True)]
        independent[r["operator"]] = [a+b for a,b in zip(independent[r["operator"]], vals)]
    official = {k: list(v) for k,v in mod.fault_counts(rows).items()}
    seeds = json.loads((root / "seeds/wave2.json").read_text())["seeds"]
    rebuilt = wave.collect(harness / "runs/wave2", harness / "runs/matrix", seeds)
    observed = {tuple(r[k] for k in keys): r for r in rows}
    reread = {tuple(r[k] for k in keys): r for r in rebuilt}
    differences = [list(k) for k in sorted(observed.keys() | reread.keys()) if observed.get(k) != reread.get(k)]
    clean = mod.clean_false_flags()
    cmd = command([sys.executable, "scripts/score_by_operator.py", "--check"], harness, out, "official-check")
    files = [path, root / "seeds/wave2.json", harness / "scripts/score_by_operator.py", harness / "scripts/score_wave2.py"]
    files += list((harness / "runs/wave2").rglob("runresult.json"))
    files += list((harness / "runs/wave2").rglob("baseline-runresult.json"))
    files += list((harness / "runs/wave2").rglob("cellverdict.json"))
    files += list((harness / "runs/matrix").rglob("cellverdict.json"))
    return {"identity": identity_report(rows, keys), "independent": independent, "official": official,
            "table_agrees": independent == official, "raw_reconstruction_differences": differences,
            "rebuilt_rows": len(rebuilt), "exclusions": dict(exclusions), "clean_false_flags": clean,
            "official_check": cmd, "empty_rate_rendering": mod.pct(0, 0),
            "perturbations": perturb(rows, "recovered", mod.fault_counts),
            "provenance": provenance(root, files)}


def main():
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise SystemExit("Run this scientific pilot in GitHub CI only")
    subject, directory, output = sys.argv[1:]
    root, out = Path(directory).resolve(), Path(output).resolve()
    out.mkdir(parents=True, exist_ok=True)
    report = {"subject": subject, "run_id": os.environ["GITHUB_RUN_ID"], "python": sys.version,
              "harness_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
              "observer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "subject_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()}
    try:
        report.update({"arb": audit_arb, "aerb": audit_aerb, "sabot": audit_sabot}[subject](root, out))
        report["execution_status"] = "completed"
    except Exception as exc:
        report.update(execution_status="inconclusive_setup_or_observer_failure", error=str(exc), traceback=traceback.format_exc())
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    # Large per-file hash inventories stay in the artifact, not the console.
    concise = {k:v for k,v in report.items() if k not in ("comparisons", "provenance", "perturbations")}
    concise["perturbation_statuses"] = {k:v["status"] for k,v in report.get("perturbations", {}).items()}
    print(json.dumps(concise, indent=2))
    return 0 if report["execution_status"] == "completed" else 1


if __name__ == "__main__":
    sys.exit(main())
