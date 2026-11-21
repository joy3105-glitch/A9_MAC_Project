from golden_model import (
    mac_fixed,
    mac_float,
    fixed_to_float,
    INPUT_WIDTH,
    INPUT_FRAC,
    PRODUCT_WIDTH,
    PRODUCT_FRAC,
    ACC_WIDTH,
    ACC_FRAC,
    OUTPUT_WIDTH,
    OUTPUT_FRAC,
    signed_range,
)

def reference_round_away(value):
    """Independent rounding: nearest, ties away from zero."""
    if value >= 0:
        return int(value + 0.5)
    return -int(-value + 0.5)


def reference_saturate(value, bits):
    """Independent signed saturation."""
    minimum = -(1 << (bits - 1))
    maximum = (1 << (bits - 1)) - 1
    return max(minimum, min(maximum, value))


def reference_rescale(value, source_frac, target_frac):
    """Independent fixed-point rescaling."""
    shift = source_frac - target_frac

    if shift > 0:
        divisor = 1 << shift
        magnitude = (abs(value) + divisor // 2) // divisor
        return magnitude if value >= 0 else -magnitude

    if shift < 0:
        return value << (-shift)

    return value


def independent_reference(A, B):
    """Independent integer-arithmetic MAC reference."""
    if len(A) != len(B):
        raise ValueError("A and B must have the same length")

    accumulator = 0
    acc_min = -(1 << (ACC_WIDTH - 1))
    acc_max = (1 << (ACC_WIDTH - 1)) - 1

    for a, b in zip(A, B):
        # Quantize inputs independently.
        a_code = reference_round_away(a * (1 << INPUT_FRAC))
        b_code = reference_round_away(b * (1 << INPUT_FRAC))

        a_code = reference_saturate(a_code, INPUT_WIDTH)
        b_code = reference_saturate(b_code, INPUT_WIDTH)

        # Multiply and limit product width.
        product = a_code * b_code
        product = reference_saturate(product, PRODUCT_WIDTH)

        # Align product and accumulator binary points.
        product = reference_rescale(
            product, PRODUCT_FRAC, ACC_FRAC
        )

        # Accumulate with saturation after each addition.
        accumulator += product
        accumulator = max(acc_min, min(acc_max, accumulator))

    # Convert accumulator to output format.
    output_code = reference_rescale(
        accumulator, ACC_FRAC, OUTPUT_FRAC
    )

    return reference_saturate(output_code, OUTPUT_WIDTH)


test_cases = [
    ([1.25], [1.0]),
    ([1.25, 2.0], [2.0, 1.5]),
    ([1.0, -1.0], [2.0, 2.0]),
    ([3.0, 2.0, 1.0], [1.0, 2.0, 3.0]),
    ([7.9], [7.9]),
    ([-8.0], [7.9]),
    ([], []),

    # Positive and negative output-rounding tie cases.
    ([0.0625], [0.5]),
    ([-0.0625], [0.5]),

    # Input quantization tie cases.
    ([0.03125], [1.0]),
    ([-0.03125], [1.0]),

     # Input overflow and boundary cases.
    ([8.0], [1.0]),        # Positive input overflow
    ([-8.5], [1.0]),       # Negative input overflow
    ([7.96875], [1.0]),    # Above positive Q4.4 maximum
    ([-8.03125], [1.0]),   # Below negative Q4.4 minimum
]


print("INDEPENDENT MAC MODEL VERIFICATION")
print("=" * 55)

all_passed = True

for index, (A, B) in enumerate(test_cases, start=1):
    actual_code = mac_fixed(A, B)
    reference_code = independent_reference(A, B)

    actual_value = fixed_to_float(actual_code, OUTPUT_FRAC)
    float_value = mac_float(A, B)
    error = abs(float_value - actual_value)

    functional_pass = actual_code == reference_code

    out_min_code, out_max_code = signed_range(OUTPUT_WIDTH)
    out_min = fixed_to_float(out_min_code, OUTPUT_FRAC)
    out_max = fixed_to_float(out_max_code, OUTPUT_FRAC)

    saturated = float_value < out_min or float_value > out_max

    print(f"\nTest {index}")
    print(f"A                   = {A}")
    print(f"B                   = {B}")
    print(f"Floating result     = {float_value:.6f}")
    print(f"Reference code      = {reference_code}")
    print(f"Actual fixed code   = {actual_code}")
    print(f"Fixed result        = {actual_value:.6f}")
    print(f"Absolute float error= {error:.6f}")
    print(f"Output saturation   = {'YES' if saturated else 'NO'}")
    print(f"Functional check    = {'PASS' if functional_pass else 'FAIL'}")

    if not functional_pass:
        all_passed = False

print("\n" + "=" * 55)
print("Overall verification:", "PASS" if all_passed else "FAIL")
print("This verifies Python fixed-point behavior, not RTL.")

if not all_passed:
    raise SystemExit(1)