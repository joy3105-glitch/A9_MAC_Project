import sys
sys.path.insert(0, "python")

from golden_model import (
    float_to_fixed,
    rescale_fixed,
    mac_fixed,
)

checks = 0

def check(name, actual, expected):
    global checks
    if actual != expected:
        raise AssertionError(
            f"{name}: actual={actual}, expected={expected}"
        )
    checks += 1
    print(f"PASS {name}: {actual}")


# 1. Rounding ties, positive and negative
for value, expected in [
    (0.5, 1),
    (-0.5, -1),
    (1.5, 2),
    (-1.5, -2),
    (2.5, 3),
    (-2.5, -3),
]:
    check(
        f"rounding {value}",
        float_to_fixed(value, 0, 8),
        expected,
    )


# 2. Rescaling with rounding
for value, expected in [
    (8, 1),
    (-8, -1),
    (7, 0),
    (-7, 0),
    (24, 2),
    (-24, -2),
]:
    check(
        f"rescale {value}",
        rescale_fixed(value, 8, 4),
        expected,
    )


# 3. Rescaling to higher fractional precision
check("left shift positive", rescale_fixed(7, 4, 8), 112)
check("left shift negative", rescale_fixed(-7, 4, 8), -112)


# 4. Accumulator overflow policies
A = [10.0, 10.0, -10.0, -10.0]
B = [10.0, 10.0, 10.0, 10.0]

common = dict(
    input_width=8,
    input_frac=0,
    product_width=16,
    product_frac=0,
    acc_width=8,
    acc_frac=0,
    output_width=8,
    output_frac=0,
)

for mode, expected in [
    ("saturate", 0),
    ("saturate_each_step", -73),
    ("wrap", 0),
]:
    check(
        f"accumulator {mode}",
        mac_fixed(A, B, acc_overflow_mode=mode, **common),
        expected,
    )


# 5. Fractional-bit configurations F1-F5
for frac in range(2, 7):
    actual = mac_fixed(
        [0.5, -0.25],
        [0.5, 0.5],
        input_width=8,
        input_frac=frac,
        product_width=16,
        product_frac=2 * frac,
        acc_width=24,
        acc_frac=8,
        output_width=8,
        output_frac=4,
    )
    check(f"F input_frac={frac}", actual, 2)


print()
print(f"NUMERIC EDGE TESTS PASS: {checks} checks")
