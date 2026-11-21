#!/usr/bin/env python3
"""A9 step 1: non-destructive Golden Model audit, with optional safe cleanup."""
import argparse
import ast
import importlib
import math
import shutil
import sys
from pathlib import Path

ROOT = Path.cwd()
PYDIR = ROOT / 'python'
GOLDEN = PYDIR / 'golden_model.py'
SPEC = PYDIR / 'numeric_spec.py'


def audit():
    for p in (GOLDEN, SPEC):
        if not p.is_file():
            raise RuntimeError(f'Missing: {p}')
        ast.parse(p.read_text(encoding='utf-8'), filename=str(p))
    sys.path.insert(0, str(PYDIR))
    importlib.invalidate_caches()
    import golden_model as g
    import numeric_spec as s
    checks = 0
    def eq(name, actual, expected):
        nonlocal checks
        checks += 1
        if actual != expected:
            raise AssertionError(f'{name}: actual={actual}, expected={expected}')
        print(f'PASS {name}: {actual}')
    eq('baseline validation', s.validate_spec(), True)
    for name, value, expected in [
        ('input max', 7.9375, 127), ('input min', -8.0, -128),
        ('positive input saturation', 20.0, 127),
        ('negative input saturation', -20.0, -128),
        ('positive quantization tie', 0.03125, 1),
        ('negative quantization tie', -0.03125, -1),
    ]:
        eq(name, g.float_to_fixed(value, 4, 8), expected)
    for value, expected in [(8, 1), (-8, -1), (7, 0), (-7, 0), (4, 0), (-4, 0)]:
        eq(f'rescale Q8->Q4 {value}', g.rescale_fixed(value, 8, 4), expected)
    eq('rescale left positive', g.rescale_fixed(7, 4, 8), 112)
    eq('rescale left negative', g.rescale_fixed(-7, 4, 8), -112)
    eq('wrap positive', g.wrap_signed(128, 8), -128)
    eq('wrap negative', g.wrap_signed(-129, 8), 127)
    eq('empty dot product', g.mac_fixed([], []), 0)
    eq('simple positive MAC', g.mac_fixed([1.0], [1.0]), 16)
    eq('simple negative MAC', g.mac_fixed([-1.0], [1.0]), -16)
    eq('float reference', g.mac_float([1.0, 2.0], [3.0, 4.0]), 11.0)
    for input_frac in range(2, 7):
        result = g.mac_fixed([0.5], [0.5], input_width=8, input_frac=input_frac,
                             product_width=16, product_frac=2*input_frac,
                             acc_width=24, acc_frac=8, output_width=8, output_frac=4)
        eq(f'F input_frac={input_frac}', result, 4)
    print(f'GOLDEN AUDIT PASS: {checks} checks')


def cleanup():
    src = GOLDEN.read_text(encoding='utf-8')
    start_marker = '    # Validate configuration.\n    widths = {'
    end_marker = '    accumulator = 0\n'
    if src.count(start_marker) != 1 or src.count(end_marker) != 1:
        raise RuntimeError('Unexpected source structure; no edits made')
    start = src.index(start_marker)
    end = src.index(end_marker, start)
    if 'validate_config(' not in src[:start]:
        raise RuntimeError('Expected central validation missing; no edits made')
    updated = src[:start] + src[end:]
    ast.parse(updated, filename=str(GOLDEN))
    backup = GOLDEN.with_name('golden_model_before_validation_cleanup.py')
    if backup.exists():
        raise RuntimeError(f'Backup already exists: {backup}; no edits made')
    shutil.copy2(GOLDEN, backup)
    GOLDEN.write_text(updated, encoding='utf-8')
    print(f'Cleaned redundant validation; backup: {backup}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--cleanup', action='store_true', help='Remove redundant validation after successful audit')
    args = parser.parse_args()
    if not GOLDEN.is_file():
        raise SystemExit('Run from ~/A9_MAC_Project')
    audit()
    if args.cleanup:
        cleanup()
        # Execute fresh interpreter so the modified module is re-imported.
        import subprocess
        result = subprocess.run([sys.executable, __file__], cwd=ROOT)
        if result.returncode:
            raise SystemExit('Post-cleanup audit FAILED; restore from the backup')
        print('POST-CLEANUP AUDIT PASS')
