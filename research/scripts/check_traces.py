"""Existential partial-observation conformance using TLC, not duplicated Python semantics."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

from check_model import JAR_SHA256, ROOT

SCENARIOS = {"human_approve", "human_deny", "evaluator_approve", "evaluator_deny", "close", "delayed_cancel", "both_enabled"}
DOMAINS = {"status": {"pending", "approved", "denied"}, "closed": {True, False},
           "phase": {"evaluating", "cancelling", "gate", "dispatched", "rejected"},
           "evaluator": {"running", "done", "cancelling", "stopped", "consumed"},
           "verdict": {"none", "approve", "deny", "escalate", "error"}}


def predicate(observation):
    values = observation["state"]
    if not values or not {"status", "closed"} <= values.keys():
        raise ValueError("Every observation must record status and closed")
    terms = []
    for key, value in values.items():
        if key not in DOMAINS or value not in DOMAINS[key]:
            raise ValueError(f"Unsupported observation: {key}={value!r}")
        literal = ("TRUE" if value else "FALSE") if key == "closed" else json.dumps(value)
        terms.append(f'{key if key == "closed" else key + "[c1]"} = {literal}')
    return " /\\ ".join(terms)


def module(observations):
    cases = '\n'.join(f'  [] cursor = {i} -> ({predicate(o)})' for i, o in enumerate(observations))
    return f'''-------------------- MODULE TraceCase --------------------
EXTENDS Approval
CONSTANT c1
VARIABLE cursor
allvars == <<vars, cursor>>
Match == CASE FALSE -> FALSE
{cases}
  [] OTHER -> FALSE
Advance == /\\ cursor < {len(observations)} /\\ Match
           /\\ cursor' = cursor + 1 /\\ UNCHANGED vars
Hidden == /\\ Next /\\ UNCHANGED cursor
TraceSpec == Init /\\ cursor = 0 /\\ [][Hidden \\/ Advance]_allvars
TraceNotMatched == cursor < {len(observations)}
==========================================================
'''


def check(jar, observations, name, expected_match):
    output = ROOT / "research/results/conformance" / name
    output.mkdir(parents=True, exist_ok=True)
    tmp = output / "tmp"
    tmp.mkdir(exist_ok=True)
    shutil.copy(ROOT / "research/models/approval/Approval.tla", output / "Approval.tla")
    (output / "TraceCase.tla").write_text(module(observations))
    (output / "TraceCase.cfg").write_text('SPECIFICATION TraceSpec\nCONSTANTS\n c1 = c1\n Calls = {c1}\n AllowOverwrite = FALSE\n BypassGate = FALSE\nINVARIANT TraceNotMatched\nCHECK_DEADLOCK FALSE\n')
    run = subprocess.run(["java", f"-Djava.io.tmpdir={tmp}", "-XX:+UseParallelGC", "-cp", str(jar),
                          "tlc2.TLC", "-workers", "1", "-seed", "1", "-config", "TraceCase.cfg", "TraceCase.tla"],
                         cwd=output, capture_output=True, text=True, timeout=120)
    log = run.stdout + run.stderr
    (output / "TLC.log").write_text(log)
    matched = run.returncode == 12 and "Invariant TraceNotMatched is violated" in log
    exhausted = run.returncode == 0 and "Model checking completed. No error has been found." in log
    if not (matched if expected_match else exhausted):
        raise RuntimeError(f"{name}: unexpected TLC result {run.returncode}; see {output}")
    return {"case": name, "expected_match": expected_match, "matched": matched, "returncode": run.returncode}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--jar", required=True, type=Path)
    p.add_argument("--traces", type=Path, default=ROOT / "research/results/traces")
    args = p.parse_args()
    jar = args.jar.resolve()
    if hashlib.sha256(jar.read_bytes()).hexdigest() != JAR_SHA256:
        raise SystemExit("Unexpected tools checksum")
    traces = [json.loads(path.read_text()) for path in sorted(args.traces.glob('*.json'))]
    if len(traces) != len(SCENARIOS) or {t.get("scenario") for t in traces} != SCENARIOS:
        raise SystemExit("Missing, duplicate, or unexpected scenario traces")
    expected_source = hashlib.sha256((ROOT / "temporal_agent_harness/harness/agent_workflow.py").read_bytes()).hexdigest()
    results = []
    for trace in traces:
        if trace.get("schema") != 1 or not trace.get("done") or trace.get("implementation_sha256") != expected_source:
            raise SystemExit("Incomplete, stale, or unsupported trace")
        observations = trace['observations']
        if not observations or observations[-1]['state'].get('phase') not in {'dispatched', 'rejected'}:
            raise SystemExit("Trace has no terminal caller observation")
        results.append(check(jar, observations, trace['scenario'], True))
    # Corrupt concrete observations, not the model: no model execution may explain these.
    bad = [{"state": {"status": "denied", "closed": False}},
           {"state": {"status": "denied", "closed": False, "phase": "dispatched"}}]
    results.append(check(jar, bad, "negative_denied_dispatch", False))
    bad = [{"state": {"status": "approved", "closed": False}},
           {"state": {"status": "pending", "closed": False}}]
    results.append(check(jar, bad, "negative_reverted_decision", False))
    out = ROOT / 'research/results/conformance/summary.json'
    out.write_text(json.dumps({"model_sha256": hashlib.sha256((ROOT / 'research/models/approval/Approval.tla').read_bytes()).hexdigest(),
                               "results": results}, indent=2) + '\n')
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
