"""Check cleanup progress and caller cancellation as separate obligations."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time

from check_model import ROOT, JAR_SHA256


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--jar',required=True,type=Path)
    jar=parser.parse_args().jar.resolve()
    if hashlib.sha256(jar.read_bytes()).hexdigest()!=JAR_SHA256:
        raise SystemExit('Pinned tools checksum mismatch')
    model=ROOT/'research/models/cancellation'
    output=ROOT/'research/results/cancellation-model'
    output.mkdir(parents=True,exist_ok=True)
    shutil.copy(ROOT/'research/models/approval/Approval.tla',output/'Approval.tla')
    shutil.copy(model/'Cleanup.tla',output/'Cleanup.tla')
    configs=[('CurrentSafety',True,True,None,None),
             ('CurrentCancellation',True,True,'CallerCancellationRespected',None),
             ('CorrectedCancellation',True,False,None,None),
             ('CurrentProgress',True,True,None,'pass'),
             ('BlockedProgress',False,True,None,'fail'),
             ('CorrectedProgress',True,False,None,'pass')]
    results=[]
    for name,finish,swallow,invariant,progress in configs:
        spec='CleanupFairSpec' if progress else 'CleanupSpec'
        checks='PROPERTIES CleanupProgress' if progress else 'INVARIANTS CleanupTypeOK DecisionStable SingleResolution AuthorizedDispatch DeniedNeverDispatches'
        if invariant or name=='CorrectedCancellation':
            checks+=' CallerCancellationRespected'
        config=f'SPECIFICATION {spec}\nCONSTANTS Calls = {{c1}}\n AllowOverwrite = FALSE\n BypassGate = FALSE\n CleanupCanFinish = {str(finish).upper()}\n SwallowCallerCancel = {str(swallow).upper()}\n{checks}\nCHECK_DEADLOCK FALSE\n'
        (output/(name+'.cfg')).write_text(config)
        start=time.monotonic()
        run=subprocess.run(['java','-XX:+UseParallelGC','-cp',str(jar),'tlc2.TLC','-workers','1','-seed','1',
                            '-config',name+'.cfg','Cleanup.tla'],cwd=output,capture_output=True,text=True,timeout=120)
        log=run.stdout+run.stderr
        (output/(name+'.log')).write_text(log)
        if invariant:
            ok=run.returncode==12 and f'Invariant {invariant} is violated' in log
        elif progress=='fail':
            ok=run.returncode==13 and 'Temporal property CleanupProgress was violated.' in log
        else:
            ok=run.returncode==0 and 'Model checking completed. No error has been found.' in log
        results.append({'configuration':name,'cleanup_can_finish':finish,'swallow_caller_cancel':swallow,
                        'returncode':run.returncode,'passed':ok,'seconds':time.monotonic()-start})
        if not ok:
            print(log[-5000:])
    summary={'model_sha256':hashlib.sha256((model/'Cleanup.tla').read_bytes()).hexdigest(),
             'base_model_sha256':hashlib.sha256((ROOT/'research/models/approval/Approval.tla').read_bytes()).hexdigest(),
             'jar_sha256':JAR_SHA256,'results':results}
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(results,indent=2))
    if not all(r['passed'] for r in results):
        raise SystemExit(1)


if __name__=='__main__':
    main()
