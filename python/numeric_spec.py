# A9 MAC - Numeric Specification
# Fixed-point format and arithmetic policies
#
# Baseline configuration:
# Input       : Q4.4
# Product     : Q8.8
# Accumulator : Q16.8
# Output      : Q4.4

# ============================================================
# 1. BASELINE CONFIGURATION
INPUT_WIDTH = 8
INPUT_FRAC = 4

PRODUCT_WIDTH = 16
PRODUCT_FRAC = 8

ACC_WIDTH = 24
ACC_FRAC = 8

OUTPUT_WIDTH = 8
OUTPUT_FRAC = 4


# 2. ARITHMETIC POLICIES
ROUNDING_MODE = "nearest_ties_away_from_zero"

INPUT_OVERFLOW_MODE = "saturate"
ACC_OVERFLOW_MODE = "saturate_each_step"
OUTPUT_OVERFLOW_MODE = "saturate"

# Supported policies
SUPPORTED_ROUNDING_MODES = {
    "truncate",
    "nearest_ties_away_from_zero",
}


SUPPORTED_OVERFLOW_MODES = {
    "saturate",
    "saturate_each_step",
    "wrap",
}

# 3. BASIC FIXED-POINT FUNCTIONS
def signed_range(bits):
    """Return signed integer minimum and maximum."""
    if not isinstance(bits, int) or bits < 2:
        raise ValueError("Signed width must be an integer >= 2")

    minimum = -(2 ** (bits - 1))
    maximum = (2 ** (bits - 1)) - 1

    return minimum, maximum


def real_range(width, frac_bits):
    """Return the representable real-number range."""
    minimum, maximum = signed_range(width)

    if not isinstance(frac_bits, int) or not 0 <= frac_bits < width:
        raise ValueError("Invalid fractional-bit allocation")

    scale = scale_factor(frac_bits)

    return minimum / scale, maximum / scale


def scale_factor(frac_bits):
    """Return the fixed-point scaling factor."""
    if not isinstance(frac_bits, int) or frac_bits < 0:
        raise ValueError("Fractional bits must be an integer >= 0")

    return 2 ** frac_bits


def format_name(width, frac_bits):
    """Return Q-format name using the project's convention."""
    signed_range(width)

    if not isinstance(frac_bits, int) or not 0 <= frac_bits < width:
        raise ValueError("Invalid fractional-bit allocation")

    return f"Q{width - frac_bits}.{frac_bits}"


# 4. CONFIGURATION VALIDATION
def validate_config(
    input_width,
    input_frac,
    product_width,
    product_frac,
    acc_width,
    acc_frac,
    output_width,
    output_frac,
    allow_product_truncation=False,
):
    """
    Validate a MAC fixed-point configuration.

    This function supports parameter sweeps.

    Product fractional bits should equal the sum of
    input fractional bits.

    Product width should preserve the full multiplication
    result unless product truncation is explicitly enabled.
    """

    widths = {
        "INPUT_WIDTH": input_width,
        "PRODUCT_WIDTH": product_width,
        "ACC_WIDTH": acc_width,
        "OUTPUT_WIDTH": output_width,
    }

    frac_bits = {
        "INPUT_FRAC": input_frac,
        "PRODUCT_FRAC": product_frac,
        "ACC_FRAC": acc_frac,
        "OUTPUT_FRAC": output_frac,
    }

    # Check widths
    for name, value in widths.items():
        if not isinstance(value, int) or value < 2:
            raise ValueError(f"{name} must be an integer >= 2")

    # Check fractional-bit allocation
    for name, value in frac_bits.items():
        if not isinstance(value, int) or value < 0:
            raise ValueError(f"{name} must be an integer >= 0")

    for name, width, frac in [
        ("INPUT", input_width, input_frac),
        ("PRODUCT", product_width, product_frac),
        ("ACC", acc_width, acc_frac),
        ("OUTPUT", output_width, output_frac),
    ]:
        if frac >= width:
            raise ValueError(
                f"{name}_FRAC must be smaller than its width"
            )

    # Multiplication scaling
    expected_product_frac = 2 * input_frac

    if product_frac != expected_product_frac:
        raise ValueError(
            "PRODUCT_FRAC must equal 2 * INPUT_FRAC"
        )

    # Full precision multiplication
    minimum_product_width = 2 * input_width

    if (
        not allow_product_truncation
        and product_width < minimum_product_width
    ):
        raise ValueError(
            "PRODUCT_WIDTH is too small for full-precision "
            "multiplication"
        )

    return True


def validate_spec():
    """Validate the baseline numeric specification."""

    validate_config(
        input_width=INPUT_WIDTH,
        input_frac=INPUT_FRAC,
        product_width=PRODUCT_WIDTH,
        product_frac=PRODUCT_FRAC,
        acc_width=ACC_WIDTH,
        acc_frac=ACC_FRAC,
        output_width=OUTPUT_WIDTH,
        output_frac=OUTPUT_FRAC,
    )

    if ROUNDING_MODE not in SUPPORTED_ROUNDING_MODES:
        raise ValueError("Unsupported rounding mode")

    if INPUT_OVERFLOW_MODE not in ("saturate", "wrap"):
        raise ValueError("Unsupported input overflow mode")

    if ACC_OVERFLOW_MODE not in (
        "saturate",
        "saturate_each_step",
        "wrap",
    ):
        raise ValueError("Unsupported accumulator overflow mode")

    if OUTPUT_OVERFLOW_MODE not in ("saturate", "wrap"):
        raise ValueError("Unsupported output overflow mode")

    return True


# 5. PRINT SPECIFICATION
def print_spec():
    """Print the baseline numeric specification."""

    print("A9 MAC NUMERIC SPECIFICATION")
    print("=" * 45)

    formats = [
        ("Input", INPUT_WIDTH, INPUT_FRAC),
        ("Product", PRODUCT_WIDTH, PRODUCT_FRAC),
        ("Accumulator", ACC_WIDTH, ACC_FRAC),
        ("Output", OUTPUT_WIDTH, OUTPUT_FRAC),
    ]

    for name, width, frac in formats:
        minimum, maximum = signed_range(width)
        real_min, real_max = real_range(width, frac)

        print(f"\n{name}")
        print(f"  Width          : {width} bits")
        print(f"  Format         : {format_name(width, frac)}")
        print(f"  Fraction bits  : {frac}")
        print(f"  Integer range  : {minimum} to {maximum}")
        print(
            f"  Real range     : "
            f"{real_min} to {real_max}"
        )
        print(f"  Scale factor   : {scale_factor(frac)}")

    print("\nArithmetic policies")
    print(f"  Rounding        : {ROUNDING_MODE}")
    print(f"  Input overflow  : {INPUT_OVERFLOW_MODE}")
    print(f"  Accumulator     : {ACC_OVERFLOW_MODE}")
    print(f"  Output overflow : {OUTPUT_OVERFLOW_MODE}")


# 6. MAIN
if __name__ == "__main__":
    validate_spec()
    print_spec()

    print("\nSpecification checks: PASS")
