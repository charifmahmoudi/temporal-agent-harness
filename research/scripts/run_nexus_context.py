"""Run the frozen Nexus context matrix; never score command failure as a bug alone."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess
import time

from prepare_nexus_context import REVISIONS

CASES = [f"nexus_context_{context}_{cache}" for context in ("completed", "open") for cache in ("cached", "cold")]


def classify(history, log, returncode, case):
    if not history or not history.get("events"):
        return {"verdict": "inconclusive", "reason": "missing history"}
    events = history["events"]
    def is_event(event, code, name):
        value = event.get("eventType", event.get("event_type"))
        return value in (code, str(code), name, "EVENT_TYPE_" + name)
    completed = any(is_event(e, 2, "WORKFLOW_EXECUTION_COMPLETED") for e in events)
    nexus_completed = any(is_event(e, 50, "NEXUS_OPERATION_COMPLETED") for e in events)
    failures = sum(is_event(e, 9, "WORKFLOW_TASK_FAILED") for e in events)
    timeouts = sum(is_event(e, 8, "WORKFLOW_TASK_TIMED_OUT") for e in events)
    raw = json.dumps(history)
    mechanism = "TMPRL1100" in raw and "non-SDK source" in raw
    if mechanism and nexus_completed:
        verdict, reason = "confirmed_mechanism", "recorded non-SDK wake after Nexus completion"
    elif returncode == 0 and completed and failures == 0 and timeouts == 0 and f"RECOVERY_PHASE {case} offline=passed" in log:
        verdict, reason = "passed", "logical payload assertion, completion, clean tasks, and offline replay passed"
    elif nexus_completed and f"RECOVERY_PHASE {case} offline=start" in log and "TMPRL1100" in log and "non-SDK source" in log:
        verdict, reason = "confirmed_mechanism", "offline phase reports non-SDK wake"
    else:
        verdict, reason = "inconclusive", "requires inspection of raw history and log"
    return {"verdict": verdict, "reason": reason, "completed": completed,
            "nexus_completed": nexus_completed, "task_failures": failures, "task_timeouts": timeouts}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdk-root", type=Path, required=True)
    parser.add_argument("--temporal", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.sdk_root = args.sdk_root.resolve()
    args.temporal = args.temporal.resolve()
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=True)
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=args.sdk_root, text=True).strip()
    if revision not in REVISIONS:
        raise ValueError("SDK revision not in frozen protocol")
    records = []
    for repetition in range(1, 4):
        for case in CASES:
            directory = args.output / f"r{repetition}" / case
            directory.mkdir(parents=True, exist_ok=True)
            env = dict(os.environ, RECOVERY_OUTPUT=str(directory), TEMPORAL_SERVICE_ADDRESS="http://127.0.0.1:7233", TEMPORAL_NAMESPACE="default", INTEG_TEMPORAL_DEV_SERVER_ON="true", RUST_LOG="info")
            server_log = (directory / "server.log").open("w")
            server = subprocess.Popen([str(args.temporal), "server", "start-dev", "--headless", "--port", "7233", "--http-port", "7243"], stdout=server_log, stderr=subprocess.STDOUT)
            record = {"case": case, "repetition": repetition, "sdk_revision": revision}
            try:
                for _ in range(60):
                    if server.poll() is not None:
                        raise RuntimeError("server exited during setup")
                    health = subprocess.run([str(args.temporal), "operator", "cluster", "health"], capture_output=True, timeout=5)
                    if health.returncode == 0:
                        break
                    time.sleep(0.5)
                else:
                    raise RuntimeError("server readiness alarm")
                version = subprocess.run([str(args.temporal), "operator", "cluster", "describe", "--output", "json"], capture_output=True, text=True, timeout=5)
                (directory / "server-version.txt").write_text(version.stdout + version.stderr)
                command = ["cargo", "integ-test", "--server-kind", "external", "--", case, "--nocapture", "--test-threads", "1"]
                record["command"] = command
                with (directory / "test.log").open("w") as log:
                    try:
                        result = subprocess.run(command, cwd=args.sdk_root, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=180)
                        record["returncode"] = result.returncode
                    except subprocess.TimeoutExpired:
                        record["returncode"] = None
                        record["invocation_alarm"] = True
                path = directory / f"{case}.json"
                history = json.loads(path.read_text()) if path.exists() else None
                record.update(classify(history, (directory / "test.log").read_text(), record["returncode"], case))
                if path.exists():
                    record["history_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            except (OSError, RuntimeError, subprocess.TimeoutExpired, json.JSONDecodeError) as error:
                record.update(verdict="inconclusive", reason=f"{type(error).__name__}: {error}")
            finally:
                server.terminate()
                try:
                    server.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.wait()
                server_log.close()
                records.append(record)
                (args.output / "summary.json").write_text(json.dumps(records, indent=2) + "\n")
                print(json.dumps(record), flush=True)


if __name__ == "__main__":
    main()
