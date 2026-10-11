"""Guard research scoring against awarding setup errors or non-assertion failures."""
import importlib.util
from pathlib import Path
import subprocess
import sys

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / 'research/scripts'
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('comparison', SCRIPTS/'compare_verification.py')
comparison = importlib.util.module_from_spec(spec)
spec.loader.exec_module(comparison)


@pytest.mark.parametrize('code,body,expected', [
    (0, '', 'survived'),
    (1, '<failure message="AssertionError">AssertionError: wrong outcome</failure>', 'detected'),
    (1, '<failure message="RuntimeError">unexpected validator exception</failure>', 'inconclusive'),
    (1, '<error message="AssertionError">fixture assertion failed</error>', 'inconclusive'),
    (0, '<skipped/>', 'inconclusive'),
    (2, '<failure message="AssertionError"/>', 'inconclusive'),
])
def test_only_valid_assertion_failure_is_detection(tmp_path, monkeypatch, code, body, expected):
    def run(*args, **kwargs):
        attr = 'failures="1"' if '<failure ' in body else 'errors="1"' if '<error ' in body else 'skipped="1"' if '<skipped' in body else ''
        (tmp_path/'results.xml').write_text(f'<testsuites><testsuite tests="1" {attr}><testcase>{body}</testcase></testsuite></testsuites>')
        return subprocess.CompletedProcess(args[0], code, 'recorded stdout', '')
    monkeypatch.setattr(comparison.subprocess, 'run', run)
    result = comparison.pytest_run(tmp_path, ['fixed_suite.py'])
    assert result['outcome'] == expected


def test_missing_junit_is_inconclusive(tmp_path, monkeypatch):
    monkeypatch.setattr(comparison.subprocess, 'run', lambda *a, **k: subprocess.CompletedProcess(a[0], 1, '', ''))
    assert comparison.pytest_run(tmp_path, ['fixed_suite.py'])['outcome'] == 'inconclusive'


def test_collector_preserves_awaits_and_drops_only_assertions():
    import ast
    tree = ast.parse('async def probe():\n    await ready()\n    assert observed == expected\n    record(observed)\n')
    transformed = comparison.Collector().visit(tree)
    assert not any(isinstance(n, ast.Assert) for n in ast.walk(transformed))
    assert len([n for n in ast.walk(transformed) if isinstance(n, ast.Await)]) == 1
    assert [n.func.id for n in ast.walk(transformed) if isinstance(n, ast.Call)] == ['record', 'ready']
