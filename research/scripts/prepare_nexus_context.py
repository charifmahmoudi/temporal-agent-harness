"""Derive matched controls from the pinned upstream async Nexus integration test."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess

REVISIONS = {
    "0689f769ccc440e8d5008d4a623dee3c82a94ff2",
    "d936c6cc6455256417c917c3637d52e53acb8178",
}
SOURCE = "crates/sdk-core/tests/integ_tests/workflow_tests/nexus.rs"
SOURCE_HASH = "f8247a0de0763bad6594a1998ac59ad6240297dee1c6326f9e2e0f26b7577dda"


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError(f"Expected one source anchor: {old!r}")
    return source.replace(old, new, 1)


def generate(source):
    if hashlib.sha256(source.encode()).hexdigest() != SOURCE_HASH:
        raise ValueError("Upstream fixture differs from the frozen source")
    start = source.index("#[workflow]\nstruct NexusAsyncWf")
    end = source.index("#[workflow]\nstruct AsyncCompleter", start)
    workflow = source[start:end].replace("NexusAsyncWf", "NexusContextWf")
    workflow = replace_once(workflow, "    outcome: Outcome,\n}",
                            "    outcome: Outcome,\n    continue_after_result: bool,\n}")
    workflow = replace_once(workflow,
        "(endpoint, schedule_to_close_timeout, outcome): (String, Option<Duration>, Outcome)",
        "(endpoint, schedule_to_close_timeout, outcome, continue_after_result): (String, Option<Duration>, Outcome, bool)")
    workflow = replace_once(workflow, "            outcome,\n", "            outcome,\n            continue_after_result,\n")
    workflow = replace_once(workflow, "        started.cancel();\n        Ok(res)",
        "        if ctx.state(|wf| wf.continue_after_result) {\n            ctx.timer(Duration::from_secs(1)).await;\n        }\n        Ok(res)")

    start = source.index("async fn nexus_async(")
    start = source.index('    let wf_name = "nexus_async";', start)
    end = source.index("#[workflow]\n#[derive(Default)]\nstruct NexusCancelBeforeStartWf", start)
    body = source[start:end].replace("NexusAsyncWf", "NexusContextWf")
    body = replace_once(body, '    let wf_name = "nexus_async";',
        '    let outcome = Outcome::Succeed;\n    let wf_name = if continue_after_result {\n        if cache_enabled { "nexus_context_open_cached" } else { "nexus_context_open_cold" }\n    } else if cache_enabled { "nexus_context_completed_cached" } else { "nexus_context_completed_cold" };')
    body = replace_once(body, "    let mut worker = starter.worker().await;",
        "    if !cache_enabled { starter.sdk_config.max_cached_workflows = 0; }\n    let mut worker = starter.worker().await;")
    body = replace_once(body, "(endpoint.clone(), schedule_to_close_timeout, outcome)",
        "(endpoint.clone(), schedule_to_close_timeout, outcome, continue_after_result)")
    body = replace_once(body,
        "    join!(nexus_task_handle, async {\n        worker.run_until_done().await.unwrap();\n    });",
        '''    let live = tokio::time::timeout(Duration::from_secs(20), async {
        join!(nexus_task_handle, async { worker.run_until_done().await.unwrap(); });
    }).await;
    let evidence_dir = std::path::PathBuf::from(std::env::var("RECOVERY_OUTPUT").expect("RECOVERY_OUTPUT is required"));
    std::fs::create_dir_all(&evidence_dir).unwrap();
    let history = starter.get_history().await;
    std::fs::write(evidence_dir.join(format!("{wf_name}.json")), serde_json::to_string_pretty(&history).unwrap()).unwrap();
    println!("RECOVERY_PHASE {wf_name} live={}", if live.is_ok() { "completed" } else { "alarm" });
    assert!(live.is_ok(), "bounded live progress alarm; inspect retained history");''')
    body = replace_once(body, "    wf_handle\n        .fetch_history_and_replay(worker.inner_mut())",
        '    println!("RECOVERY_PHASE {wf_name} offline=start");\n    wf_handle\n        .fetch_history_and_replay(worker.inner_mut())')
    body = replace_once(body, "        .await\n        .unwrap();\n}\n", 
        '        .await\n        .unwrap();\n    println!("RECOVERY_PHASE {wf_name} offline=passed");\n}\n')
    functions = "\n".join(
        f"#[tokio::test]\nasync fn nexus_context_{context}_{cache}() {{ run_nexus_context({cont}, {cached}).await; }}"
        for context, cont in [("completed", "false"), ("open", "true")]
        for cache, cached in [("cached", "true"), ("cold", "false")]
    )
    return source + "\n" + workflow + "\nasync fn run_nexus_context(continue_after_result: bool, cache_enabled: bool) {\n" + body + functions + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdk-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=args.sdk_root, text=True).strip()
    if revision not in REVISIONS:
        raise ValueError(f"Unapproved source revision: {revision}")
    path = args.sdk_root / SOURCE
    source = path.read_text()
    generated = generate(source)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "fixture.rs").write_text(generated)
    (args.output / "provenance.json").write_text(json.dumps({
        "sdk_revision": revision, "upstream_sha256": SOURCE_HASH,
        "generated_sha256": hashlib.sha256(generated.encode()).hexdigest(),
        "source_path": SOURCE,
        "fixture_origin": "upstream NexusAsyncWf and nexus_async; MIT license retained in SDK checkout",
        "changes": ["success-only controls", "explicit continuation input", "omit cancel after completed result", "cache treatment", "bounded live alarm", "history retention"],
    }, indent=2) + "\n")
    path.write_text(generated)
    (args.output / "fixture.patch").write_text(subprocess.check_output(
        ["git", "diff", "--", SOURCE], cwd=args.sdk_root, text=True))


if __name__ == "__main__":
    main()
