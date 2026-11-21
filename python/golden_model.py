from numeric_spec import (
    INPUT_WIDTH,
    INPUT_FRAC,
    PRODUCT_WIDTH,
    PRODUCT_FRAC,
    ACC_WIDTH,
    ACC_FRAC,
    OUTPUT_WIDTH,
    OUTPUT_FRAC,
    signed_range,
    validate_spec,
    ROUNDING_MODE,
    INPUT_OVERFLOW_MODE,
    ACC_OVERFLOW_MODE,
    OUTPUT_OVERFLOW_MODE,
    SUPPORTED_ROUNDING_MODES,
    SUPPORTED_OVERFLOW_MODES,
    validate_config,
)

def wrap_signed(value, bits):
    """Wrap an integer to signed two's-complement width."""
    value = int(value)
    modulus = 1 << bits
    return ((value + (1 << (bits - 1))) % modulus) - (1 << (bits - 1))


def apply_overflow(value, bits, mode):
    """Apply a selected signed overflow policy."""
    if mode in ("saturate", "saturate_each_step"):
        return saturate(value, bits)

    if mode == "wrap":
        return wrap_signed(value, bits)

    raise ValueError(f"Unsupported overflow mode: {mode}")

def saturate(value, bits):
    """Clamp an integer to the signed range of the given width."""
    minimum, maximum = signed_range(bits)
    return max(minimum, min(maximum, int(value)))


def round_away_from_zero(value):
    """Round to nearest; exact ties go away from zero."""
    if value >= 0:
        return int(value + 0.5)
    return -int(-value + 0.5)


def float_to_fixed(
    value,
    frac_bits,
    bits,
    rounding_mode=ROUNDING_MODE,
    overflow_mode="saturate",
):
    """Convert a real number to a fixed-point integer code."""

    if rounding_mode not in SUPPORTED_ROUNDING_MODES:
        raise ValueError(f"Unsupported rounding mode: {rounding_mode}")

    signed_range(bits)

    if (
        not isinstance(frac_bits, int)
        or isinstance(frac_bits, bool)
        or not 0 <= frac_bits < bits
    ):
        raise ValueError("Invalid fractional-bit allocation")

    scaled = value * (2 ** frac_bits)

    if rounding_mode == "truncate":
        quantized = int(scaled)
    else:
        quantized = round_away_from_zero(scaled)

    return apply_overflow(quantized, bits, overflow_mode)


def fixed_to_float(value, frac_bits):
    return value / (2 ** frac_bits)


def rescale_fixed(
    value,
    source_frac,
    target_frac,
    rounding_mode=ROUNDING_MODE,
):
    """Rescale fixed-point value using a selected rounding mode."""

    if rounding_mode not in SUPPORTED_ROUNDING_MODES:
        raise ValueError(f"Unsupported rounding mode: {rounding_mode}")

    for name, frac in (
        ("source_frac", source_frac),
        ("target_frac", target_frac),
    ):
        if (
            not isinstance(frac, int)
            or isinstance(frac, bool)
            or frac < 0
        ):
            raise ValueError(f"{name} must be a non-negative integer")

    shift = source_frac - target_frac

    if shift == 0:
        return value

    if shift < 0:
        return value << (-shift)

    divisor = 1 << shift
    magnitude = abs(value)

    if rounding_mode == "truncate":
        result = magnitude // divisor
    else:
        result = (magnitude + divisor // 2) // divisor

    return result if value >= 0 else -result


def mac_fixed(
    A,
    B,
    input_width=INPUT_WIDTH,
    input_frac=INPUT_FRAC,
    acc_width=ACC_WIDTH,
    acc_frac=ACC_FRAC,
    output_width=OUTPUT_WIDTH,
    output_frac=OUTPUT_FRAC,
    product_width=None,
    product_frac=None,
    rounding_mode=ROUNDING_MODE,
    input_overflow_mode=INPUT_OVERFLOW_MODE,
    acc_overflow_mode=ACC_OVERFLOW_MODE,
    output_overflow_mode=OUTPUT_OVERFLOW_MODE,
):
    """
    Fixed-point MAC model with configurable bit widths.

    A and B contain real-number inputs.
    The returned value is the signed integer output code.

    If product_width/product_frac are omitted, they are derived
    from input_width/input_frac.
    """

    if rounding_mode not in SUPPORTED_ROUNDING_MODES:
        raise ValueError("Unsupported rounding mode")

    if input_overflow_mode not in ("saturate", "wrap"):
        raise ValueError("Unsupported input overflow mode")

    if acc_overflow_mode not in (
        "saturate",
        "saturate_each_step",
        "wrap",
    ):
        raise ValueError("Unsupported accumulator overflow mode")

    if output_overflow_mode not in ("saturate", "wrap"):
        raise ValueError("Unsupported output overflow mode")

    if len(A) != len(B):
        raise ValueError("A and B must have the same length")

    # Derive product format from the input format unless specified.
    if product_width is None:
        product_width = 2 * input_width

    if product_frac is None:
        product_frac = 2 * input_frac

    # Validate the complete MAC configuration.
    validate_config(
        input_width=input_width,
        input_frac=input_frac,
        product_width=product_width,
        product_frac=product_frac,
        acc_width=acc_width,
        acc_frac=acc_frac,
        output_width=output_width,
        output_frac=output_frac,
    )

    accumulator = 0
    acc_min, acc_max = signed_range(acc_width)

    for a, b in zip(A, B):
        # Convert real inputs to fixed-point codes.
        a_fixed = float_to_fixed(
            a, input_frac, input_width,
            rounding_mode, input_overflow_mode
        )

        b_fixed = float_to_fixed(
            b, input_frac, input_width,
            rounding_mode, input_overflow_mode
        )

        # Multiply and limit product width.
        product = a_fixed * b_fixed
        product = saturate(product, product_width)

        # Align product fractional precision with the accumulator.
        product = rescale_fixed(
            product, product_frac, acc_frac, rounding_mode
        )

        # Accumulate with saturation after every addition.
        accumulator += product

        if acc_overflow_mode == "saturate_each_step":
            accumulator = saturate(accumulator, acc_width)

        elif acc_overflow_mode == "wrap":
            accumulator = wrap_signed(accumulator, acc_width)

    if acc_overflow_mode == "saturate":
        accumulator = saturate(accumulator, acc_width)

    # Convert accumulator to output format.
    output_code = rescale_fixed(
        accumulator, acc_frac, output_frac, rounding_mode
    )

    return apply_overflow(
        output_code, output_width, output_overflow_mode
    )


def mac_float(A, B):
    """Floating-point reference for the dot product."""
    if len(A) != len(B):
        raise ValueError("A and B must have the same length")

    return sum(a * b for a, b in zip(A, B))


def run_tests():
    """Run basic checks for the default fixed-point configuration."""
    validate_spec()

    test_cases = [
        ([1.25, 2.0, -1.5, 0.75],
         [2.0, 1.5, 2.0, -1.0]),
        ([1.0], [1.0]),
        ([-1.0], [1.0]),
        ([0.0], [5.0]),
        ([7.9], [7.9]),
        ([-8.0], [7.9]),
        ([], []),
    ]

    print("A9 GOLDEN MODEL TESTS")
    print("=" * 50)

    for index, (A, B) in enumerate(test_cases, start=1):
        fixed_code = mac_fixed(A, B)
        fixed_value = fixed_to_float(fixed_code, OUTPUT_FRAC)
        float_value = mac_float(A, B)
        error = abs(float_value - fixed_value)

        print(f"\nTest {index}")
        print(f"  A                = {A}")
        print(f"  B                = {B}")
        print(f"  Floating result  = {float_value:.6f}")
        print(f"  Fixed output code= {fixed_code}")
        print(f"  Fixed result     = {fixed_value:.6f}")
        print(f"  Absolute error   = {error:.6f}")

    assert round_away_from_zero(2.5) == 3
    assert round_away_from_zero(-2.5) == -3
    assert saturate(200, OUTPUT_WIDTH) == 127
    assert saturate(-200, OUTPUT_WIDTH) == -128

    print("\nRounding and saturation checks: PASS")
    print("Golden model tests completed.")


if __name__ == "__main__":
    run_tests()
