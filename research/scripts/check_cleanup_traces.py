"""Check retained caller-cancellation observations against executable Cleanup.tla.

This is retrospective, bounded conformance, not extraction or refinement. Inputs
cannot be invented by hidden transitions. Both model variants consume the same data.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

from check_model import ROOT, JAR_SHA256

sys.path.insert(0, str(ROOT))
from tests.cancellation.audit import validate_audit


def require(condition, message):
    if not condition:
        raise ValueError(message)


def project(record):
    """Only the two observed, completing caller-cancellation scenarios are supported."""
    before, after = record['before'], record['after']
    for state in (before, after):
        require(state['status'] in {'approved', 'denied'}, 'invalid status')
        require(state['closed'] is False and state['started'] is True,
                'requires open session with started evaluator')
        require(state['cleanup_entered'] is True, 'cleanup was not observed')
    require(before['done'] is False and before['outcome'] is None, 'caller already finished')
    require(before['caller_cancel_requested'] is False and before['second_cancel'] is False,
            'cancellation already observed before boundary')
    require(after['caller_cancel_requested'] is True and after['second_cancel'] is True,
            'requires delivered caller cancellation and child response')
    require(after['done'] is True and after['outcome'] in {'dispatched', 'cancelled'},
            'unsupported final observation')
    events = after['events']
    validate_audit(events)
    require(events[:len(before['events'])] == before['events'], 'event prefix changed')
    types = [e['type'] for e in events]
    relevant = ('tool_approval_requested', 'auto_approval_evaluation_started',
                'tool_approval_resolved', 'auto_approval_evaluation_superseded')
    require(all(types.count(t) == 1 for t in relevant), 'missing or duplicate lifecycle event')
    indices = [types.index(t) for t in relevant]
    require(indices == sorted(indices), 'lifecycle events reordered')
    require(indices[2] < len(before['events']) <= indices[3], 'settlement/cleanup boundary moved')
    require(all(e.get('tool_id') == 'call' for e in events if e['type'] in relevant),
            'unexpected call identity')
    starts = [i for i, t in enumerate(types) if t == 'tool_start']
    require(len(starts) == int(after['outcome'] == 'dispatched'), 'outcome/tool-start disagreement')
    require(not starts or starts[0] > indices[3], 'dispatch preceded cleanup terminal')
    approved = events[indices[2]]['approved']
    require(type(approved) is bool, 'decision must be Boolean')
    # The delayed evaluator has not completed at before; only cleanup is pending.
    # Final status/outcome come from data, never from the expected source variant.
    return [
        {'action': 'approve' if approved else 'deny',
         'state': {'status': before['status'], 'closed': False}},
        {'action': 'snapshot', 'state': {'status': before['status'], 'closed': False,
         'phase': 'cancelling', 'cleanupPending': True, 'callerCancelled': False,
         'outcome': 'none'}},
        {'action': 'cancel', 'state': {'callerCancelled': True}},
        {'action': 'snapshot', 'state': {'status': after['status'], 'closed': False,
         'callerCancelled': True, 'cleanupPending': False, 'outcome': after['outcome']}},
    ]


def module(observations):
    actions = {'approve': '(Human(c1,"approved") /\\ UNCHANGED <<callerCancelled,outcome,cleanupPending>>)',
               'deny': '(Human(c1,"denied") /\\ UNCHANGED <<callerCancelled,outcome,cleanupPending>>)',
               'cancel': 'CancelCaller', 'snapshot': 'UNCHANGED cleanupVars'}
    domains = {'status': {'pending','approved','denied'}, 'phase': {'evaluating','cancelling','gate','aborted','dispatched','rejected'},
               'closed': {True,False}, 'callerCancelled': {True,False}, 'cleanupPending': {True,False},
               'outcome': {'none','dispatched','rejected','cancelled'}}
    definitions, steps = [], []
    for i, observation in enumerate(observations):
        terms = []
        for key, value in observation['state'].items():
            require(key in domains and value in domains[key], 'unsupported model observation')
            literal = str(value).upper() if isinstance(value, bool) else json.dumps(value)
            terms.append(f'{key + "[c1]" if key in {"status","phase"} else key} = {literal}')
        definitions.append(f'Observed{i} == ' + ' /\\ '.join(terms))
        steps.append(f'(cursor = {i} /\\ ({actions[observation["action"]]}) /\\ Observed{i}\' /\\ cursor\' = {i+1})')
    return '\n'.join(['---------------- MODULE CleanupTrace ----------------', 'EXTENDS Cleanup',
        'CONSTANT c1', 'VARIABLE cursor', 'allvars == <<cleanupVars,cursor>>', *definitions,
        'Advance == ' + '\n \\/ '.join(steps),
        # No Environment, Human, Complete, Close, or CancelCaller can be hidden.
        'Hidden == (ConsumeStep \\/ FinishCleanup \\/ FinalizeStep) /\\ UNCHANGED cursor',
        'TraceSpec == CleanupInit /\\ cursor = 0 /\\ [][Advance \\/ Hidden]_allvars',
        f'TraceNotMatched == cursor < {len(observations)}', '====================================================']) + '\n'


def run_case(jar, output, name, observations, swallow, expected):
    folder = output / name
    folder.mkdir(parents=True, exist_ok=True)
    for rel in ('approval/Approval.tla', 'cancellation/Cleanup.tla'):
        shutil.copy(ROOT/'research/models'/rel, folder/Path(rel).name)
    (folder/'observations.json').write_text(json.dumps(observations, indent=2)+'\n')
    (folder/'CleanupTrace.tla').write_text(module(observations))
    (folder/'CleanupTrace.cfg').write_text(
        'SPECIFICATION TraceSpec\nCONSTANTS c1 = c1\n Calls = {c1}\n AllowOverwrite = FALSE\n'
        ' BypassGate = FALSE\n CleanupCanFinish = TRUE\n SwallowCallerCancel = '+str(swallow).upper()+
        '\nINVARIANT TraceNotMatched\nCHECK_DEADLOCK FALSE\n')
    (folder/'tmp').mkdir(exist_ok=True)
    run = subprocess.run(['java',f'-Djava.io.tmpdir={folder}/tmp','-XX:+UseParallelGC','-cp',str(jar),'tlc2.TLC','-workers','1','-seed','1',
                          '-config','CleanupTrace.cfg','CleanupTrace.tla'],cwd=folder,capture_output=True,text=True,timeout=120)
    log = run.stdout+run.stderr
    (folder/'TLC.log').write_text(log)
    matched = run.returncode == 12 and 'Invariant TraceNotMatched is violated' in log
    exhausted = run.returncode == 0 and 'Model checking completed. No error has been found.' in log
    require(matched if expected else exhausted, f'{name}: unexpected TLC result; see {folder}/TLC.log')
    return {'case':name,'swallow_caller_cancel':swallow,'expected_match':expected,'matched':matched,
            'returncode':run.returncode,'observations_sha256':hashlib.sha256((folder/'observations.json').read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--jar', required=True, type=Path)
    args = parser.parse_args()
    jar = args.jar.resolve()
    require(hashlib.sha256(jar.read_bytes()).hexdigest() == JAR_SHA256, 'tools checksum mismatch')
    metadata = json.loads((ROOT/'research/evaluation/cancellation-results.json').read_text())
    artifact = metadata['artifacts']['implementation']
    archive = ROOT/'research/evaluation'/artifact['file']
    require(hashlib.sha256(archive.read_bytes()).hexdigest() == artifact['sha256'], 'archive checksum mismatch')
    output = ROOT/'research/results/cleanup-conformance'
    output.mkdir(parents=True,exist_ok=True)
    rows, sources, records = [], [], {}
    with zipfile.ZipFile(archive) as z:
        for variant in ('baseline','corrected'):
            for response in ('second_raise','second_return'):
                matches = [n for n in z.namelist() if f'/{variant}/' in n and n.endswith(f'/caller-{response}.json')]
                require(len(matches) == 1, 'missing/duplicate retained case')
                raw = z.read(matches[0]); record = json.loads(raw)
                require(record['variant'] == variant and record['source_sha256'] == metadata['source_hashes'][variant+'_sha256'],
                        'source provenance mismatch')
                trace = project(record); name = variant+'-'+response
                records[name] = record
                sources.append({'case':name,'member':matches[0],'sha256':hashlib.sha256(raw).hexdigest(),
                                'source_sha256':record['source_sha256']})
                rows.append(run_case(jar,output,name,trace,variant=='baseline',True))
                rows.append(run_case(jar,output,name+'-wrong-model',trace,variant!='baseline',False))
    base = project(records['baseline-second_raise'])
    invalid = {}
    t = deepcopy(base); t[0],t[2] = t[2],t[0]; invalid['cancel-before-approval'] = t
    t = deepcopy(base); t[0]['action'] = 'snapshot'; invalid['invented-approval'] = t
    t = deepcopy(base); t[0]['action'] = 'deny'; invalid['wrong-recorded-decision'] = t
    t = deepcopy(base); t[-1]['state']['status'] = 'denied'; invalid['rewritten-decision'] = t
    for name,trace in invalid.items():
        rows.append(run_case(jar,output,name,trace,True,False))
    rejected = []
    for name in ('missing-child-response','duplicate-resolution','early-tool-start',
                 'wrong-tool-identity','wrong-evaluation-identity','duplicate-ended','duplicate-error'):
        record = deepcopy(records['baseline-second_raise'])
        if name == 'missing-child-response': record['after']['second_cancel'] = False
        elif name == 'duplicate-resolution':
            record['after']['events'].append(next(e for e in record['after']['events'] if e['type']=='tool_approval_resolved'))
        elif name == 'wrong-tool-identity':
            next(e for e in record['after']['events'] if e['type']=='tool_start')['tool_id'] = 'unrelated-call'
        elif name == 'wrong-evaluation-identity':
            next(e for e in record['after']['events'] if e['type']=='auto_approval_evaluation_superseded')['evaluation_id'] = 'unrelated-evaluation'
        elif name.startswith('duplicate-'):
            event = deepcopy(next(e for e in record['after']['events'] if e['type']=='auto_approval_evaluation_superseded'))
            if name == 'duplicate-ended':
                event.update(type='auto_approval_evaluation_ended', verdict='deny', reason=None, details={})
            else:
                event.pop('verdict', None)
                event.update(type='auto_approval_evaluation_error', message='synthetic control')
            record['after']['events'].append(event)
        else:
            events = record['after']['events']; index = next(i for i,e in enumerate(events) if e['type']=='tool_start')
            event = events.pop(index); events.insert(len(record['before']['events']),event)
        try: project(record)
        except ValueError as exc: rejected.append({'case':name,'reason':str(exc)})
        else: raise ValueError('projection accepted '+name)
    result = {'schema':1,'archive_sha256':artifact['sha256'],'jar_sha256':JAR_SHA256,
              'model_sha256':hashlib.sha256((ROOT/'research/models/cancellation/Cleanup.tla').read_bytes()).hexdigest(),
              'base_model_sha256':hashlib.sha256((ROOT/'research/models/approval/Approval.tla').read_bytes()).hexdigest(),
              'checker_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'sources':sources,'results':rows,'projection_rejections':rejected}
    (output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Cleanup: 4 retained traces matched, 8 model controls rejected, 7 invalid records rejected.')


if __name__ == '__main__': main()
