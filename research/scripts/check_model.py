"""Run completed TLC checks and require specific synthetic-fault counterexamples."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
MODEL = ROOT / "research/models/approval"
JAR_SHA256 = "7beec0f04818732a62fa193731711a99aa4f11279499b2360a7d156c519ea78d"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--jar", type=Path, required=True)
    args = parser.parse_args()
    jar = args.jar.resolve()
    if hashlib.sha256(jar.read_bytes()).hexdigest() != JAR_SHA256:
        raise SystemExit("Unexpected TLA+ tools JAR: expected pinned v1.8.0 asset")
    output = ROOT / "research/results/latest"
    output.mkdir(parents=True, exist_ok=True)
    tmp = output / "tmp"
    tmp.mkdir(exist_ok=True)
    command = ["java", f"-Djava.io.tmpdir={tmp}", "-XX:+UseParallelGC", "-cp", str(jar)]
    results = []
    checks = [("Safety", None), ("TwoCalls", None), ("Liveness", None),
              ("Overwrite", "SingleResolution"), ("Bypass", "AuthorizedDispatch")]
    for name, expected in checks:
        start = time.monotonic()
        try:
            run = subprocess.run(command + ["tlc2.TLC", "-workers", "1", "-seed", "1",
                                 "-config", f"{name}.cfg", "Approval.tla"],
                                 cwd=MODEL, capture_output=True, text=True, timeout=120)
            log = run.stdout + run.stderr
            (output / f"{name}.log").write_text(log)
            if expected:
                ok = run.returncode == 12 and f"Invariant {expected} is violated" in log
            else:
                ok = run.returncode == 0 and "Model checking completed. No error has been found." in log
            results.append(dict(configuration=name, expected_violation=expected,
                                returncode=run.returncode, passed=ok,
                                seconds=time.monotonic() - start))
        except subprocess.TimeoutExpired:
            results.append(dict(configuration=name, passed=False, error="timeout"))
    metadata = dict(commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                    model_sha256=hashlib.sha256((MODEL / "Approval.tla").read_bytes()).hexdigest(),
                    jar_sha256=JAR_SHA256,
                    java=subprocess.run(["java", "-version"], capture_output=True, text=True).stderr,
                    checks=results)
    (output / "summary.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps(results, indent=2))
    if not all(item["passed"] for item in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
