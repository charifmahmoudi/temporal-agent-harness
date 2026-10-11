"""Reproducible lexical inventory for a manually reviewed repair boundary.

This is NOT a semantic slicer. Calls are unresolved syntax, lambdas are deferred,
and no safety/replay verdict is emitted. Standard library only.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path

from prepare_cancellation_variant import corrected, SOURCE

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / 'research/evaluation/repair-boundary.json'
PATCH_ID = 'approval-caller-cancel-v1'
TARGETS = (
    '_cancel_and_settle', '_apply_approval_policy',
    'AgentWorkflowRunner._run_auto_mode_evaluator',
    'AgentWorkflowRunner._handle_tool_approval',
    'AgentWorkflowRunner._resolve_and_publish',
    'activity_tool_defn.decorator.dispatch',
)


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def definitions(tree):
    result = {}

    def walk(node, prefix=()):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            prefix = (*prefix, node.name)
            if not isinstance(node, ast.ClassDef):
                name = '.'.join(prefix)
                result.setdefault(name, []).append(node)
        for child in ast.iter_child_nodes(node):
            walk(child, prefix)

    walk(tree)
    return result


def inventory(source, name):
    candidates = definitions(ast.parse(source))[name]
    if len(candidates) != 1:
        raise ValueError(f'ambiguous definition: {name}')
    node = candidates[0]
    facts = {key: [] for key in ('awaits', 'handlers', 'guards', 'calls', 'reads', 'deferred')}

    def add(key, n, value):
        facts[key].append({'line': n.lineno, 'text': value})

    def walk(n):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            add('deferred', n, getattr(n, 'name', '<lambda>'))
            return
        if isinstance(n, ast.Await):
            add('awaits', n, ast.unparse(n.value))
        if isinstance(n, ast.ExceptHandler):
            add('handlers', n, ast.unparse(n.type) if n.type else 'BaseException (bare except)')
        if isinstance(n, (ast.If, ast.IfExp, ast.While)):
            add('guards', n, ast.unparse(n.test))
        if isinstance(n, ast.Call):
            add('calls', n, ast.unparse(n.func))
        if isinstance(n, ast.Attribute) and isinstance(n.ctx, ast.Load):
            add('reads', n, ast.unparse(n))
        for child in ast.iter_child_nodes(n):
            walk(child)

    for statement in node.body:
        walk(statement)
    return {
        'definition': name, 'lines': [node.lineno, node.end_lineno],
        'ast_sha256': digest(ast.dump(node, include_attributes=False)),
        **facts,
    }


def build():
    baseline = (ROOT / SOURCE).read_text()
    fixed = corrected(baseline)
    anchor = 'if caller is not None and caller.cancelling():'
    if fixed.count(anchor) != 1:
        raise ValueError('versioned guard anchor drifted')
    versioned = fixed.replace(anchor,
        'if caller is not None and caller.cancelling() and (\n'
        f'        not workflow.in_workflow() or workflow.patched("{PATCH_ID}")\n'
        '    ):')
    return {
        'schema': 1,
        'kind': 'lexical inventory; manually selected boundary; no semantic slice claim',
        'source_path': str(SOURCE),
        'script_sha256': digest(Path(__file__).read_text()),
        'variant_generator_sha256': digest((ROOT / 'research/scripts/prepare_cancellation_variant.py').read_text()),
        'analysis_status': 'unsupported for automatic safety or replay certification',
        'open_obligations': [
            'Resolve dynamic evaluator and runner calls, aliases, and publication effects.',
            'Give deferred wait predicates and concurrent handlers scheduler semantics.',
            'Relate caller cancellation count to delivered requests and uncancel operations.',
            'Model exception propagation, child suppression, and successful cleanup return.',
            'Model SDK patch memoization, activation callback, markers, and replay cursor.',
            'Preserve activity command identity, arguments, options, and effect boundary.',
        ],
        'variants': [
            {'name': label, 'source_sha256': digest(source),
             'functions': [inventory(source, name) for name in names]}
            for label, source, names in (
                ('baseline', baseline, TARGETS),
                ('corrected', fixed, (TARGETS[0], TARGETS[2])),
                ('versioned', versioned, (TARGETS[0],)),
            )
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = build()
    if args.check:
        if json.loads(OUTPUT.read_text()) != result:
            raise SystemExit('Repair boundary inventory drifted; review before regenerating')
    else:
        OUTPUT.write_text(json.dumps(result, indent=2) + '\n')
    print('9 function inventories checked; semantic certification remains unsupported')


if __name__ == '__main__':
    main()
