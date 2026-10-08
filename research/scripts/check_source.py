"""Detect AST drift in mapped methods; this does not automatically extract a model."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "research/models/approval/source-map.json"


def digests():
    module = ast.parse((ROOT / "temporal_agent_harness/harness/agent_workflow.py").read_text())
    targets = {
        "_apply_approval_policy", "_cancel_and_settle",
        "_WorkflowStatus.register_pending_approval", "_WorkflowStatus.resolve_approval",
        "_WorkflowStatus.finalize_approval", "_WorkflowStatus.is_approval_resolved",
        "AgentWorkflowRunner._validate_tool_approval", "AgentWorkflowRunner._handle_tool_approval",
        "AgentWorkflowRunner._run_auto_mode_evaluator", "AgentWorkflowRunner._handle_close",
        "AgentWorkflowRunner._resolve_and_publish",
    }
    found = {}
    for node in module.body:
        nodes = [(node.name, node)] if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) else []
        if isinstance(node, ast.ClassDef):
            nodes = [(f"{node.name}.{n.name}", n) for n in node.body
                     if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        for name, function in nodes:
            if name in targets:
                # Ignore comments/docstrings and line numbers; preserve executable AST.
                if (function.body and isinstance(function.body[0], ast.Expr)
                        and isinstance(function.body[0].value, ast.Constant)
                        and isinstance(function.body[0].value.value, str)):
                    function.body = function.body[1:]
                found[name] = hashlib.sha256(ast.dump(function, include_attributes=False).encode()).hexdigest()
    if set(found) != targets:
        raise SystemExit(f"Missing mapped methods: {targets - set(found)}")
    return found


if __name__ == "__main__":
    expected = json.loads(MANIFEST.read_text())["ast_sha256"]
    actual = digests()
    changed = [name for name in actual if actual[name] != expected.get(name)]
    if changed:
        raise SystemExit(f"Review model correspondence before refreshing hashes: {changed}")
    print(f"Mapped executable AST unchanged ({len(actual)} methods).")
