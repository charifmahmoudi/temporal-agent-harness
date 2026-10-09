"""Render a human-readable comparison from a committed evidence snapshot."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = ROOT / 'research/evaluation/results-v1.json'
REPORT = ROOT / 'research/evaluation/results-v1.md'


def render(data):
    rows = data['results']
    faults = [r for r in rows if r['fault'] != 'baseline']
    lines = ['# Comparative evaluation — results v1', '',
             '[Case study](../../RESEARCH.md) · [Protocol](protocol.md) · [Evidence snapshot](results-v1.json)', '',
             'This report is generated from the committed JSON snapshot; edit interpretation',
             'in [Assessment](assessment.md), not the measurements here.', '',
             f"Execution commit: `{data['execution_commit']}`.",
             f"Artifact baseline: `{data['baseline_commit']}`.",
             f"Corpus SHA-256: `{data['corpus_sha256']}`.",
             f"[CI evidence]({data['evidence_url']}).", '',
             '## Detection matrix', '',
             '| Python implementation | Existing tests | Expanded tests | Recorded-input trace checking |',
             '| --- | --- | --- | --- |']
    for row in rows:
        cells = [row['fault']] + [row[a]['outcome'].replace('_', ' ') for a in ('existing','expanded','trace')]
        lines.append('| ' + ' | '.join(cells) + ' |')
    lines += ['', 'The baseline must survive all arms. “Detected” means a valid assertion failure',
              'or completed TLC rejection. “Inconclusive” is not detection or survival.',
              '“Out of scope” preserves the model exclusion.', '', '## Totals', '',
              '| Arm | Detected | Survived | Inconclusive | Out of scope |',
              '| --- | --- | --- | --- | --- |']
    for arm in ('existing','expanded','trace'):
        counts = [sum(r[arm]['outcome']==o for r in faults) for o in ('detected','survived','inconclusive','out_of_scope')]
        lines.append('| '+arm+' | '+' | '.join(map(str,counts))+' |')
    unique = [r['fault'] for r in faults if r['trace']['outcome']=='detected' and
              r['existing']['outcome']=='survived' and r['expanded']['outcome']=='survived']
    lines += ['', 'Trace-only detections with both test arms successfully surviving: '+
              (', '.join(unique) if unique else '**none**')+'.', '',
              'This comparison has six Python faults; five have a model-covered trace arm.',
              'The unchanged model does not consume Python mutations. The separate model',
              'experiment has 13 configurations and five abstract-fault controls; those',
              'are not Python-fault detections in this matrix.', '', '## Single-run wall times', '',
              '| Fault | Existing tests (s) | Expanded tests (s) | Collector + TLC (s) |',
              '| --- | --- | --- | --- |']
    for row in faults:
        times = [f"{row[a]['seconds']:.2f}" if 'seconds' in row[a] else '—' for a in ('existing','expanded','trace')]
        lines.append('| '+row['fault']+' | '+' | '.join(times)+' |')
    lines += ['', 'Times include subprocess execution and exclude package-copy preparation.',
              'They are one observation on one runner, not a performance benchmark.',
              'The JSON retains per-trace outcomes, counts, runtime versions, and hashes.',
              'Raw logs and JUnit evidence remain in the linked CI artifact.', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    text = render(json.loads(SNAPSHOT.read_text()))
    if args.check:
        if REPORT.read_text() != text:
            raise SystemExit('Comparison report drifted; regenerate it from its snapshot')
        print('Comparison report matches its evidence snapshot.')
    else:
        REPORT.write_text(text)


if __name__ == '__main__':
    main()
