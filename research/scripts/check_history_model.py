"""Check the boundary model and bind 36 retained replay cells to model states."""
import argparse
import base64
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

from check_model import ROOT, JAR_SHA256
from check_cleanup_traces import require


def observations():
    meta = json.loads((ROOT/'research/evaluation/activity-results.json').read_text())
    path = ROOT/'research/evaluation'/meta['archive']
    require(hashlib.sha256(path.read_bytes()).hexdigest() == meta['archive_sha256'], 'archive hash mismatch')
    rows = []
    with zipfile.ZipFile(path) as z:
        for target in ('baseline','corrected','versioned'):
            replay = json.loads(z.read(target+'-replay.json'))
            require(len(replay['rows']) == 12, 'missing replay cells')
            for row in replay['rows']:
                raw = z.read('histories/'+row['history'])
                require(hashlib.sha256(raw).hexdigest() == row['history_sha256'], 'history hash mismatch')
                history = json.loads(raw)['events']
                origin, scenario = row['history'].removesuffix('.history.json').split('--')
                result = json.loads(z.read('cases/'+origin+'--'+scenario+'/result.json'))
                signals = [e for e in history if e.get('workflowExecutionSignaledEventAttributes',{}).get('signalName') == 'cancel_caller']
                scheduled = [e for e in history if e.get('eventType') == 'EVENT_TYPE_ACTIVITY_TASK_SCHEDULED']
                patches = []
                for event in history:
                    marker = event.get('markerRecordedEventAttributes',{})
                    if marker.get('markerName') == 'core_patch':
                        patches.append(json.loads(base64.b64decode(marker['details']['patch-data']['payloads'][0]['data'])))
                require(patches in ([],[{'id':'approval-caller-cancel-v1','deprecated':False}]), 'unsupported marker')
                require(len(signals) <= 1 and len(scheduled) <= 1, 'unsupported history multiplicity')
                require(bool(signals) == result['state']['caller_cancel_requested'], 'signal/state disagreement')
                if signals:
                    require(result['state']['second_cancel'] is True, 'child response not observed')
                if signals and scheduled:
                    require(int(signals[0]['eventId']) < int(scheduled[0]['eventId']), 'cancel must precede activity')
                ledger_path = 'cases/'+origin+'--'+scenario+'/ledger.jsonl'
                ledger = z.read(ledger_path).splitlines() if ledger_path in z.namelist() else []
                require(len(ledger) <= 1, 'single-attempt bound exceeded')
                require(result['state']['status'] in {'approved','denied'}, 'unknown status')
                require(row['command'] in {'compatible','nondeterministic'}, 'inconclusive replay')
                rows.append({'id':origin+'--'+scenario+'--'+target,'producer':origin,'target':target,
                             'approved':result['state']['status']=='approved','cancelled':bool(signals),
                             'command':bool(scheduled),'marker':bool(patches),'effect':len(ledger),
                             'compatible':row['command']=='compatible','history_sha256':row['history_sha256']})
    require(len({r['id'] for r in rows}) == 36, 'duplicate/missing cells')
    return meta, rows


def evidence_module(rows):
    records = []
    for row in rows:
        fields = []
        for key,value in row.items():
            if key == 'history_sha256': continue
            literal = str(value).upper() if isinstance(value,bool) else json.dumps(value)
            fields.append(key+' |-> '+literal)
        records.append('['+', '.join(fields)+']')
    return '''----------------------- MODULE HistoryEvidence -----------------------
EXTENDS History
Rows == {'''+',\n'.join(records)+'''}
EvidenceAgreement == pc = "done" =>
  \\A r \\in Rows :
    (producer = r.producer /\\ target = r.target /\\ approved = r.approved /\\ cancelled = r.cancelled)
    => (command = r.command /\\ marker = r.marker /\\ effect = r.effect /\\ compatible = r.compatible)
=============================================================================
'''


def run_case(jar, output, name, invariant, expected_failure=False, fault=False, rows=None):
    folder = output/name
    folder.mkdir(parents=True,exist_ok=True); (folder/'tmp').mkdir(exist_ok=True)
    shutil.copy(ROOT/'research/models/history/History.tla', folder/'History.tla')
    module = 'History'
    if rows is not None:
        module = 'HistoryEvidence'
        (folder/(module+'.tla')).write_text(evidence_module(rows))
    (folder/(module+'.cfg')).write_text('SPECIFICATION Spec\nCONSTANT DuplicateReplayEffect = '+str(fault).upper()+
                                      '\nINVARIANTS TypeOK '+invariant+'\nCHECK_DEADLOCK FALSE\n')
    run = subprocess.run(['java',f'-Djava.io.tmpdir={folder}/tmp','-XX:+UseParallelGC','-cp',str(jar),'tlc2.TLC',
                          '-workers','1','-seed','1','-config',module+'.cfg',module+'.tla'],
                         cwd=folder,capture_output=True,text=True,timeout=120)
    log = run.stdout+run.stderr; (folder/'TLC.log').write_text(log)
    failure = run.returncode == 12 and f'Invariant {invariant} is violated' in log
    success = run.returncode == 0 and 'Model checking completed. No error has been found.' in log
    require(failure if expected_failure else success, f'{name}: unexpected TLC result; see {folder}/TLC.log')
    return {'case':name,'invariant':invariant,'expected_failure':expected_failure,'returncode':run.returncode,'passed':True}


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--jar',required=True,type=Path)
    jar = parser.parse_args().jar.resolve()
    require(hashlib.sha256(jar.read_bytes()).hexdigest() == JAR_SHA256,'tools checksum mismatch')
    meta, rows = observations()
    output = ROOT/'research/results/history-model'; output.mkdir(parents=True,exist_ok=True)
    (output/'observations.json').write_text(json.dumps(rows,indent=2)+'\n')
    results = []
    cases = [('AuthorizedCommand',False),('NoReplayEffect',False),('BaselineFreshCancellation',True),
             ('DirectFreshCancellation',False),('VersionedFreshCancellation',False),
             ('DirectPreservesBaseline',True),('VersionedPreservesBaseline',False),
             ('VersionedPreservesUnmarkedCorrection',True)]
    for invariant,expected in cases:
        results.append(run_case(jar,output,invariant,invariant,expected))
    results.append(run_case(jar,output,'duplicate-effect-fault','NoReplayEffect',True,True))
    results.append(run_case(jar,output,'retained-evidence','EvidenceAgreement',rows=rows))
    for field in ('command','compatible'):
        altered = deepcopy(rows); altered[0][field] = not altered[0][field]
        results.append(run_case(jar,output,'wrong-'+field,'EvidenceAgreement',True,rows=altered))
    result = {'schema':1,'archive_sha256':meta['archive_sha256'],'jar_sha256':JAR_SHA256,
              'model_sha256':hashlib.sha256((ROOT/'research/models/history/History.tla').read_bytes()).hexdigest(),
              'checker_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'observations_sha256':hashlib.sha256((output/'observations.json').read_bytes()).hexdigest(),
              'cells':len(rows),'results':results}
    (output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print('History: 12 expected TLC results, including agreement with all 36 retained replay cells.')


if __name__ == '__main__': main()
