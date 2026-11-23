"""Summarize A9 MAC P0/P1/P2 results from existing Yosys logs and test logs.
Run from anywhere: python3 path/to/summary_p0_p1_p2_verified.py --root ~/A9_MAC_Project
"""
import argparse
import csv
import re
from pathlib import Path

CONFIGS = ('C1', 'C2', 'C3', 'C4', 'C5')
ARCH = {'p0': ('yosys_{c}.log', 'equiv_{c}_rerun.log', 'EQUIVALENCE RESULT: PASS', 1),
        'p1': ('yosys_P1_{c}.log', 'pipeline_stream_{c}.log', 'PIPELINE STREAMING TEST: PASS', 2),
        'p2': ('yosys_P2_{c}.log', 'pipeline2_stream_{c}.log', 'P2 PIPELINE STREAMING TEST: PASS', 3)}

def synthesis(path):
    text = path.read_text(errors='replace')
    sections = re.findall(r'===\s+\S+\s+===([\s\S]*?)(?=\n===\s+|\Z)', text)
    if not sections:
        raise ValueError(f'Cannot find module statistics: {path}')
    found = []
    for section in sections:
        cells = re.findall(r'Number of cells:\s*(\d+)', section)
        ff = re.findall(r'^\s+\$_[A-Z0-9_]*DFF[A-Z0-9_]*\s+(\d+)\s*$', section, re.M)
        if cells:
            found.append((int(cells[-1]), sum(map(int, ff))))
    if not found:
        raise ValueError(f'Cannot find cell counts: {path}')
    return found[-1]

def status(path, marker):
    if not path.exists():
        return 'MISSING', None, None
    txt = path.read_text(errors='replace')
    errors = re.findall(r'Errors\s*:\s*(\d+)', txt)
    checks = re.findall(r'(?:Output checks|Total vectors)\s*:\s*(\d+)', txt)
    passed = marker in txt and errors and int(errors[-1]) == 0
    return ('PASS' if passed else 'FAIL'), (int(checks[-1]) if checks else None), (int(errors[-1]) if errors else None)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path.cwd(), help='Project root')
    parser.add_argument('--output', type=Path, help='Output CSV path')
    args = parser.parse_args()
    root = args.root.expanduser().resolve()
    results = root / 'results'
    with (results / 'bitwidth_sweep.csv').open(newline='') as f:
        accuracy = {row['name']: row for row in csv.DictReader(f)}
    rows = []
    for c in CONFIGS:
        row = {'config': c}
        for k in ('input_width','input_frac','product_width','acc_width','mae','rmse','max_error'):
            row[k] = accuracy[c][k]
        for arch, (syn_file, test_file, marker, latency) in ARCH.items():
            cells, ff = synthesis(results / syn_file.format(c=c))
            test_status, checks, errors = status(results / test_file.format(c=c), marker)
            row.update({f'{arch}_cells': cells, f'{arch}_ff': ff,
                        f'{arch}_latency_cycles': latency, f'{arch}_ii_cycles': 1,
                        f'{arch}_verification_status': test_status,
                        f'{arch}_output_checks': checks, f'{arch}_errors': errors})
        rows.append(row)
    output = args.output or (results / 'summary_p0_p1_p2_verified.csv')
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f'Saved: {output}')
    print('Config | P0 cells/FF | P1 cells/FF | P2 cells/FF | Verification P0/P1/P2')
    for r in rows:
        print(f"{r['config']:>6} | {r['p0_cells']:>5}/{r['p0_ff']:<3} | "
              f"{r['p1_cells']:>5}/{r['p1_ff']:<3} | {r['p2_cells']:>5}/{r['p2_ff']:<3} | "
              f"{r['p0_verification_status']}/{r['p1_verification_status']}/{r['p2_verification_status']}")
    if any(r[f'{a}_verification_status'] != 'PASS' for r in rows for a in ARCH):
        raise SystemExit('WARNING: Some verification logs are missing or failed')

if __name__ == '__main__':
    main()
