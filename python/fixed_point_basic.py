TOTAL_BITS = 8
FRAC_BITS = 4

MAX_INT = 2 ** (TOTAL_BITS - 1) - 1
MIN_INT = -2 ** (TOTAL_BITS - 1)

SCALE = 2 ** FRAC_BITS


def float_to_fixed(x):
    """
    Chuyển số thực sang số nguyên fixed-point Q4.4.
    """

    value = round(x * SCALE)

    # Saturation
    if value > MAX_INT:
        value = MAX_INT

    if value < MIN_INT:
        value = MIN_INT

    return value


def fixed_to_float(x):
    """
    Chuyển số nguyên fixed-point về số thực.
    """

    return x / SCALE


def quantization_error(x):
    """
    Tính sai số lượng tử hóa.
    """

    x_fixed = float_to_fixed(x)

    x_recovered = fixed_to_float(x_fixed)

    return x - x_recovered


# Các giá trị kiểm tra
test_values = [
    0.0,
    0.5,
    1.0,
    1.25,
    1.2375,
    2.5,
    -1.5,
    -2.75,
    7.5,
    -8.0
]


print("======================================")
print("       FIXED-POINT BASIC TEST")
print("======================================")

print("Q-format:", f"Q{TOTAL_BITS - FRAC_BITS}.{FRAC_BITS}")
print("Total bits:", TOTAL_BITS)
print("Fraction bits:", FRAC_BITS)
print("Scale:", SCALE)

print()

print(
    f"{'Float':>10} "
    f"{'Fixed':>10} "
    f"{'Recovered':>12} "
    f"{'Error':>12}"
)

print("-" * 50)


for x in test_values:

    fixed = float_to_fixed(x)

    recovered = fixed_to_float(fixed)

    error = x - recovered

    print(
        f"{x:10.4f} "
        f"{fixed:10d} "
        f"{recovered:12.4f} "
        f"{error:12.6f}"
    )
