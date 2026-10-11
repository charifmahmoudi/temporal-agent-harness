"""Run explicit review stages against the frozen subject; never label them independent.

Use --stage plan to inspect commands. A reviewer supplies identity and a new output
folder. This wrapper is not part of the subject's verification method.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

REVISION = 'ccb74997404f6b9fd9f5654ac5a441337581d673'
JAR_SHA256 = '7beec0f04818732a62fa193731711a99aa4f11279499b2360a7d156c519ea78d'


def commands(subject, python, jar, stage):
    def step(name, argv, cwd=None, env=None):
        return {'name': name, 'argv': [str(a) for a in argv],
                'cwd': str(cwd or subject), 'env': env or {}}
    if stage == 'audit':
        return [step('documentation', [sys.executable,'research/scripts/check_documentation.py']),
                step('source-map', [sys.executable,'research/scripts/check_source.py'])]
    if stage == 'models':
        return [step(name,[sys.executable,'research/scripts/'+name+'.py','--jar',jar]) for name in
                ('check_model','check_cascade','check_cancellation_model','check_cleanup_traces','check_history_model')]
    if stage == 'activity':
        out = subject/'research/results/activity-upgrade'
        return [step('scoring',[python,'-m','pytest','tests/activity_upgrade/test_scoring.py','-q']),
                step('fresh-activity-and-replay',[python,'research/scripts/run_activity_study.py']),
                step('versioned-regressions',[python,'run_regressions.py',out/'versioned-manifest.json',out/'versioned-regressions.xml'],
                     out/'variants/versioned',{'PYTHONPATH':str(out/'variants/versioned')})]
    if stage == 'cancellation':
        out = subject/'research/results/cancellation-corrected'
        return [step('baseline',[python,'-m','pytest','tests/cancellation/','-q',
                                  '--junitxml=research/results/cancellation-baseline.xml']),
                step('prepare-correction',[sys.executable,'research/scripts/prepare_cancellation_variant.py','--output',out]),
                step('corrected',[python,'run.py','tests/cancellation/','-q','--junitxml=results.xml'],out,
                     {'PYTHONPATH':str(out),'CANCELLATION_VARIANT':'corrected'}),
                step('corrected-regressions',[python,'run.py','tests/harness/','-q','--junitxml=harness-results.xml'],out,
                     {'PYTHONPATH':str(out)})]
    raise ValueError(stage)


def git(subject, *args):
    return subprocess.check_output(['git',*args],cwd=subject,text=True).strip()


def interpreter_path(subject, explicit=None):
    """Preserve executable symlinks: resolving a venv Python loses its environment."""
    return Path(os.path.abspath(explicit)) if explicit else subject / ".venv/bin/python"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--subject',type=Path,required=True)
    parser.add_argument('--stage',choices=['plan','audit','models','activity','cancellation'],required=True)
    parser.add_argument('--jar',type=Path)
    parser.add_argument('--python',type=Path,help='Frozen subject venv Python, required for live stages')
    parser.add_argument('--output',type=Path,help='New directory outside the subject')
    parser.add_argument('--reviewer',help='Identity or explicitly self-test; does not establish independence')
    args = parser.parse_args()
    subject = args.subject.resolve()
    python = interpreter_path(subject, args.python)
    jar = args.jar.resolve() if args.jar else Path('/path/to/pinned/tla2tools.jar')
    plan = {stage:commands(subject,python,jar,stage) for stage in ('audit','models','activity','cancellation')}
    if args.stage == 'plan':
        print(json.dumps({'subject_revision':REVISION,'stages':plan},indent=2)); return
    if not args.output or not args.reviewer:
        parser.error('Execution requires --output and --reviewer; use self-test for author runs')
    if git(subject,'rev-parse','HEAD') != REVISION:
        raise SystemExit('Subject must be exactly '+REVISION)
    if git(subject,'status','--porcelain','--untracked-files=normal'):
        raise SystemExit('Use a clean subject checkout; record modifications as a separate follow-up')
    output = args.output.resolve()
    if output == subject or subject in output.parents:
        raise SystemExit('Choose an output directory outside the subject checkout')
    if args.stage == 'models' and (not jar.is_file() or hashlib.sha256(jar.read_bytes()).hexdigest()!=JAR_SHA256):
        raise SystemExit('Provide the checksum-matching TLA+ tools JAR')
    if args.stage in {'activity','cancellation'} and not python.is_file():
        raise SystemExit('Provide the frozen subject environment with --python')
    if args.stage in {'activity','cancellation'}:
        locations = ['activity-upgrade'] if args.stage=='activity' else ['cancellation','cancellation-corrected']
        if any((subject/'research/results'/name).exists() for name in locations):
            raise SystemExit('Live output already exists; preserve it and use a fresh subject checkout')
    output.mkdir(parents=True,exist_ok=False)
    selected = plan[args.stage]
    summary = {'schema':1,'subject_revision':REVISION,'stage':args.stage,'reviewer':args.reviewer,
               'independence':'not assessed by this runner','utc_started':datetime.now(timezone.utc).isoformat(),
               'platform':platform.platform(),'driver_python':sys.version,'lock_sha256':hashlib.sha256((subject/'uv.lock').read_bytes()).hexdigest(),
               'driver_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'results':[]}
    (output/'plan.json').write_text(json.dumps(selected,indent=2)+'\n')
    try:
        for index,item in enumerate(selected):
            log = output/f'{index:02d}-{item["name"]}.log'
            print('Running '+item['name'],flush=True)
            # Exclude a caller's PYTHONPATH; only isolated variants set one explicitly.
            env = dict(os.environ); env.pop('PYTHONPATH',None); env.pop('CANCELLATION_VARIANT',None)
            env.update(item['env'])
            result = {'name':item['name'],'log':log.name,'returncode':None,'status':'inconclusive'}
            try:
                with log.open('w') as stream:
                    run = subprocess.run(item['argv'],cwd=item['cwd'],env=env,stdout=stream,
                                         stderr=subprocess.STDOUT,timeout=1800)
                result.update(returncode=run.returncode,status='completed' if run.returncode==0 else 'failed')
            except (OSError,subprocess.TimeoutExpired) as exc:
                result['error'] = str(exc)
            result['log_sha256'] = hashlib.sha256(log.read_bytes()).hexdigest() if log.exists() else None
            summary['results'].append(result)
            if result['status'] != 'completed': break
    finally:
        summary['all_commands_completed'] = len(summary['results'])==len(selected) and all(r['status']=='completed' for r in summary['results'])
        summary['utc_finished'] = datetime.now(timezone.utc).isoformat()
        (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print('Retain '+str(output)+' and the subject research/results directory. Complete the human response template separately.')
    if not summary['all_commands_completed']: raise SystemExit(1)


if __name__ == '__main__': main()
