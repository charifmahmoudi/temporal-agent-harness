"""Prepare a provenance-checked isolated correction; never edit production source."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import shutil

from check_model import ROOT

SOURCE=Path('temporal_agent_harness/harness/agent_workflow.py')
BEFORE='''    task.cancel()
    try:
        await task
    except (Exception, asyncio.CancelledError):
        pass
'''
AFTER='''    caller = asyncio.current_task()
    task.cancel()
    try:
        await task
    except (Exception, asyncio.CancelledError):
        pass
    # Child cleanup cannot consume an outstanding cancellation of its caller.
    # Check after a normal return too: a child may suppress the second request.
    if caller is not None and caller.cancelling():
        raise asyncio.CancelledError
'''
BEFORE_EVALUATOR='''            await _cancel_and_settle(task)
            close(
                AutoApprovalEvaluationSuperseded(
                    tool_id=tool_id,
                    tool_name=ctx.tool_name,
                    evaluation_id=evaluation_id,
                    evaluator=evaluator,
                    verdict=reached,
                )
            )
'''
AFTER_EVALUATOR='''            terminal = AutoApprovalEvaluationSuperseded(
                tool_id=tool_id,
                tool_name=ctx.tool_name,
                evaluation_id=evaluation_id,
                evaluator=evaluator,
                verdict=reached,
            )
            try:
                await _cancel_and_settle(task)
            except asyncio.CancelledError:
                # A live caller cancellation closes this already-settled bracket.
                # Offline eviction must not publish on a destroyed workflow loop.
                if workflow.in_workflow():
                    close(terminal)
                raise
            close(terminal)
'''


def corrected(source):
    if source.count(BEFORE)!=1 or source.count(BEFORE_EVALUATOR)!=1:
        raise ValueError('Cleanup helper anchor drifted; review the proposed correction')
    return source.replace(BEFORE,AFTER).replace(BEFORE_EVALUATOR,AFTER_EVALUATOR)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    out=args.output.resolve()
    # Restrict deletion/recreation to this study's reproducible output directory.
    if out != (ROOT/'research/results/cancellation-corrected').resolve():
        raise SystemExit('Use research/results/cancellation-corrected for isolated output')
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    for folder in ('temporal_agent_harness','tests'):
        shutil.copytree(ROOT/folder,out/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    shutil.copy(ROOT/'pyproject.toml',out/'pyproject.toml')
    original=(ROOT/SOURCE).read_text()
    fixed=corrected(original)
    (out/SOURCE).write_text(fixed)
    diff=''.join(difflib.unified_diff(original.splitlines(keepends=True),fixed.splitlines(keepends=True),
                                     fromfile='a/'+str(SOURCE),tofile='b/'+str(SOURCE),n=1))
    (out/'proposed.patch').write_text(diff)
    (out/'provenance.json').write_text(json.dumps({'baseline_sha256':hashlib.sha256(original.encode()).hexdigest(),
                                                 'corrected_sha256':hashlib.sha256(fixed.encode()).hexdigest()},indent=2)+'\n')
    # Executed from the isolated cwd; source path and bytes must be the correction.
    (out/'run.py').write_text('''from pathlib import Path
import hashlib, json, sys
import temporal_agent_harness.harness.agent_workflow as impl
expected=Path('temporal_agent_harness/harness/agent_workflow.py').resolve()
if Path(impl.__file__).resolve()!=expected: raise RuntimeError('Wrong imported package')
if hashlib.sha256(expected.read_bytes()).hexdigest()!=json.loads(Path('provenance.json').read_text())['corrected_sha256']: raise RuntimeError('Wrong source bytes')
import pytest
sys.exit(pytest.main(sys.argv[1:]))
''')
    print(json.dumps({'isolated_directory':str(out),'production_changed':False}))


if __name__=='__main__':
    main()
