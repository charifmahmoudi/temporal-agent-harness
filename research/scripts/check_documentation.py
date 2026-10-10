"""Check local scientific-document links, reproducible figures, and result report."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def main():
    files = [ROOT/'RESEARCH.md', *sorted((ROOT/'research').rglob('*.md'))]
    # Generated TLC/isolated experiment directories are not repository documents.
    files = [p for p in files if 'results' not in p.relative_to(ROOT).parts]
    count = 0
    for path in files:
        for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
            if '://' in target or target.startswith('#'):
                continue
            destination = target.split('#')[0]
            if not (path.parent/destination).exists():
                raise SystemExit(f'{path.relative_to(ROOT)}: missing {target}')
            count += 1
    figures = sorted((ROOT/'research/figures').glob('*.svg'))
    before = {p:p.read_bytes() for p in figures}
    subprocess.run([sys.executable, str(ROOT/'research/figures/generate.py')], check=True)
    if any(p.read_bytes()!=data for p,data in before.items()):
        raise SystemExit('Figure output drifted from its generator; review and commit regeneration')
    snapshot = json.loads((ROOT/'research/evaluation/results-v1.json').read_text())
    corpus_path = ROOT/'research/evaluation/corpus.json'
    corpus = json.loads(corpus_path.read_text())
    if snapshot['corpus_sha256'] != hashlib.sha256(corpus_path.read_bytes()).hexdigest():
        raise SystemExit('Frozen v1 corpus differs from measured evidence')
    expected = {'baseline', *[f['id'] for f in corpus['faults']]}
    rows = snapshot['results']
    if len(rows) != len(expected) or {r['fault'] for r in rows} != expected:
        raise SystemExit('Comparison snapshot omits or duplicates a planned fault')
    if snapshot['source_sha256'] != corpus['baseline_source_sha256']:
        raise SystemExit('Evidence baseline hash mismatch')
    subprocess.run([sys.executable, str(ROOT/'research/scripts/render_comparison.py'), '--check'], check=True)
    subprocess.run([sys.executable, str(ROOT/'research/scripts/render_cancellation.py'), '--check'], check=True)
    subprocess.run([sys.executable, str(ROOT/'research/scripts/render_upgrade.py'), '--check'], check=True)
    subprocess.run([sys.executable, str(ROOT/'research/scripts/render_activity.py'), '--check'], check=True)
    subprocess.run([sys.executable, str(ROOT/'research/scripts/render_model_bridges.py'), '--check'], check=True)
    subprocess.run([sys.executable, str(ROOT/'research/scripts/check_repair_observability.py'), '--check'], check=True)
    subprocess.run([sys.executable, str(ROOT/'research/scripts/extract_repair_boundary.py'), '--check'], check=True)
    subprocess.run([sys.executable, str(ROOT/'research/scripts/test_repair_boundary.py')], check=True)
    subprocess.run([sys.executable, str(ROOT/'research/scripts/compare_repair_encodings.py'), '--check'], check=True)
    subprocess.run([sys.executable, str(ROOT/'research/scripts/test_repair_encodings.py')], check=True)
    subprocess.run([sys.executable, str(ROOT/'research/scripts/check_composition_argument.py')], check=True)
    print(f'{count} relative documentation links resolve; figure outputs are reproducible.')


if __name__ == '__main__':
    main()
