"""Enumerate a declared continuation grammar; no automatic grammar inference."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from prepare_nexus_context import REVISIONS, SOURCE, SOURCE_HASH, generate, replace_once

HOST = "crates/sdk/src/workflow_future.rs"
HOST_HASH = "7ebd1993362fea6632a19f6896cb672ae93679082c643ff6117e3483f142f390"
SUFFIXES = ("return", "state", "timer0", "timer1")


def fixture(source):
    generated = generate(source)
    generated = generated[:generated.index("\n#[tokio::test]\nasync fn nexus_context_completed_cached")]
    generated = generated.replace("NexusContextWf", "NexusContinuationWf")
    generated = generated.replace("continue_after_result", "continuation")
    generated = replace_once(generated, "    continuation: bool,", "    continuation: u8,")
    generated = replace_once(generated, "Option<Duration>, Outcome, bool)", "Option<Duration>, Outcome, u8)")
    generated = replace_once(generated,
        "async fn run_nexus_context(continuation: bool, cache_enabled: bool)",
        "async fn run_nexus_continuation(continuation: u8, cache_enabled: bool)")
    generated = replace_once(generated,
        '''    let wf_name = if continuation {
        if cache_enabled { "nexus_context_open_cached" } else { "nexus_context_open_cold" }
    } else if cache_enabled { "nexus_context_completed_cached" } else { "nexus_context_completed_cold" };''',
        '''    let wf_name = match (continuation, cache_enabled) {
        (0, true) => "nexus_continuation_return_cached",
        (0, false) => "nexus_continuation_return_cold",
        (1, true) => "nexus_continuation_state_cached",
        (1, false) => "nexus_continuation_state_cold",
        (2, true) => "nexus_continuation_timer0_cached",
        (2, false) => "nexus_continuation_timer0_cold",
        (3, true) => "nexus_continuation_timer1_cached",
        (3, false) => "nexus_continuation_timer1_cold",
        _ => unreachable!(),
    };''')
    generated = replace_once(generated,
        '''        if ctx.state(|wf| wf.continuation) {
            ctx.timer(Duration::from_secs(1)).await;
        }
        Ok(res)''',
        '''        println!("CONTINUATION_PHASE result replay={} suffix={}", ctx.is_replaying(), ctx.state(|wf| wf.continuation));
        match ctx.state(|wf| wf.continuation) {
            0 => {},
            1 => { assert!(!ctx.state(|wf| wf.endpoint.is_empty())); },
            2 => { ctx.timer(Duration::ZERO).await; },
            3 => { ctx.timer(Duration::from_secs(1)).await; },
            _ => unreachable!(),
        }
        println!("CONTINUATION_PHASE returned replay={}", ctx.is_replaying());
        Ok(res)''')
    functions = "\n".join(
        f"#[tokio::test]\nasync fn nexus_continuation_{suffix}_{cache}() {{ run_nexus_continuation({index}, {cached}).await; }}"
        for index, suffix in enumerate(SUFFIXES)
        for cache, cached in (("cached", "true"), ("cold", "false")))
    return generated + functions + "\n"


def diagnostic(source):
    if hashlib.sha256(source.encode()).hexdigest() != HOST_HASH:
        raise ValueError("Unexpected host source")
    source = replace_once(source, "            let run_id = activation.run_id.clone();",
        '            let run_id = activation.run_id.clone();\n            println!("CONTINUATION_HOST run={} replay={} eviction={}", run_id, activation.is_replaying, is_only_eviction);')
    source = replace_once(source,
        "                .is_some_and(|t| t.take_non_sdk_wake())\n            {",
        '                .is_some_and(|t| t.take_non_sdk_wake())\n            {\n                println!("CONTINUATION_WAKE_FAILURE run={} replay={}", run_id, activation.is_replaying);')
    return source


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdk-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=args.sdk_root, text=True).strip()
    if revision not in REVISIONS:
        raise ValueError("Unapproved SDK revision")
    args.output.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for path, transform in ((SOURCE, fixture), (HOST, diagnostic)):
        target = args.sdk_root / path
        generated = transform(target.read_text())
        target.write_text(generated)
        hashes[path] = hashlib.sha256(generated.encode()).hexdigest()
        (args.output / target.name).write_text(generated)
    (args.output / "provenance.json").write_text(json.dumps({"sdk_revision": revision,
        "upstream_sha256": SOURCE_HASH, "host_sha256": HOST_HASH,
        "generated_hashes": hashes, "grammar": SUFFIXES,
        "instrumented": True, "origin": "frozen upstream MIT-licensed Nexus fixture"}, indent=2) + "\n")
    (args.output / "fixture.patch").write_text(subprocess.check_output(
        ["git", "diff", "--", SOURCE, HOST], cwd=args.sdk_root, text=True))


if __name__ == "__main__":
    main()
