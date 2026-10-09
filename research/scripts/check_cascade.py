"""Check coupled policy semantics, retaining the original Approval module as input."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from check_model import ROOT, JAR_SHA256


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--jar', required=True, type=Path)
    jar = parser.parse_args().jar.resolve()
    if hashlib.sha256(jar.read_bytes()).hexdigest() != JAR_SHA256:
        raise SystemExit('Unexpected TLA+ tools checksum')
    source = ROOT / 'research/models/cascade'
    out = ROOT / 'research/results/cascade'
    out.mkdir(parents=True, exist_ok=True)
    tmp = out / 'tmp'
    tmp.mkdir(exist_ok=True)
    shutil.copy(ROOT / 'research/models/approval/Approval.tla', out / 'Approval.tla')
    shutil.copy(source / 'Cascade.tla', out / 'Cascade.tla')
    checks = [('SameTool', None), ('DifferentTools', None), ('Liveness', None),
              ('LeakScope', 'ScopePreserved'), ('OverwriteSettled', 'SingleResolution'),
              ('ReverseCause', 'CauseBeforeCascade')]
    results = []
    for name, violation in checks:
        shutil.copy(source / f'{name}.cfg', out / f'{name}.cfg')
        run = subprocess.run(['java', f'-Djava.io.tmpdir={tmp}', '-XX:+UseParallelGC', '-cp', str(jar),
                              'tlc2.TLC', '-workers', '1', '-seed', '1', '-config', f'{name}.cfg', 'Cascade.tla'],
                             cwd=out, capture_output=True, text=True, timeout=120)
        log = run.stdout + run.stderr
        (out / f'{name}.log').write_text(log)
        ok = (run.returncode == 12 and f'Invariant {violation} is violated' in log) if violation else (
            run.returncode == 0 and 'Model checking completed. No error has been found.' in log)
        results.append(dict(configuration=name, passed=ok, expected_violation=violation, returncode=run.returncode))
    metadata = {'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                'module_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in [out / 'Cascade.tla', out / 'Approval.tla']},
                'checks': results}
    (out / 'summary.json').write_text(json.dumps(metadata, indent=2) + '\n')
    print(json.dumps(results, indent=2))
    if not all(item['passed'] for item in results):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
