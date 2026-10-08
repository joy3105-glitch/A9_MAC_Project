# ==========================================
# A9 MAC GOLDEN MODEL
# ==========================================


INPUT_WIDTH = 8
INPUT_FRAC = 4

PRODUCT_WIDTH = 16
PRODUCT_FRAC = 8

ACC_WIDTH = 24
ACC_FRAC = 8

OUTPUT_WIDTH = 8
OUTPUT_FRAC = 4


# ==========================================
# Signed range
# ==========================================

def get_signed_range(bits):

    minimum = -(2 ** (bits - 1))

    maximum = 2 ** (bits - 1) - 1

    return minimum, maximum


# ==========================================
# Float -> Fixed
# ==========================================

def float_to_fixed(x, frac_bits, bits):

    scale = 2 ** frac_bits

    value = round(x * scale)

    minimum, maximum = get_signed_range(bits)

    value = max(
        minimum,
        min(maximum, value)
    )

    return value


# ==========================================
# Fixed -> Float
# ==========================================

def fixed_to_float(x, frac_bits):

    return x / (2 ** frac_bits)


# ==========================================
# Saturation
# ==========================================

def saturate(value, bits):

    minimum, maximum = get_signed_range(bits)

    return max(
        minimum,
        min(maximum, value)
    )


# ==========================================
# Fixed-point MAC
# ==========================================

def mac_fixed(A, B):

    # --------------------------------------
    # Convert inputs to fixed-point
    # --------------------------------------

    A_fixed = [
        float_to_fixed(
            x,
            INPUT_FRAC,
            INPUT_WIDTH
        )
        for x in A
    ]


    B_fixed = [
        float_to_fixed(
            x,
            INPUT_FRAC,
            INPUT_WIDTH
        )
        for x in B
    ]


    # --------------------------------------
    # Accumulator
    # --------------------------------------

    accumulator = 0


    for a, b in zip(A_fixed, B_fixed):

        # Multiplication
        product = a * b

        # Accumulation
        accumulator += product


    # --------------------------------------
    # Accumulator saturation
    # --------------------------------------

    accumulator = saturate(
        accumulator,
        ACC_WIDTH
    )


    # --------------------------------------
    # Q*.8 -> Q*.4
    # --------------------------------------

    shift = ACC_FRAC - OUTPUT_FRAC


    if shift > 0:

        rounding_value = 1 << (shift - 1)


        if accumulator >= 0:

            accumulator = (
                accumulator +
                rounding_value
            ) >> shift

        else:

            accumulator = (
                accumulator -
                rounding_value
            ) >> shift


    # --------------------------------------
    # Output saturation
    # --------------------------------------

    output = saturate(
        accumulator,
        OUTPUT_WIDTH
    )


    return output


# ==========================================
# Floating-point reference
# ==========================================

def mac_float(A, B):

    result = 0.0


    for a, b in zip(A, B):

        result += a * b


    return result


# ==========================================
# Test Golden Model
# ==========================================

if __name__ == "__main__":

    A = [
        1.25,
        2.0,
        -1.5,
        0.75
    ]


    B = [
        2.0,
        1.5,
        2.0,
        -1.0
    ]


    # Ideal floating-point result

    float_result = mac_float(
        A,
        B
    )


    # Fixed-point result

    fixed_result = mac_fixed(
        A,
        B
    )


    # Convert fixed result to float

    fixed_float = fixed_to_float(
        fixed_result,
        OUTPUT_FRAC
    )


    print("======================================")
    print("          GOLDEN MAC MODEL")
    print("======================================")

    print()

    print("A =", A)

    print("B =", B)

    print()

    print(
        "Float MAC result :",
        float_result
    )

    print(
        "Fixed MAC result :",
        fixed_result
    )

    print(
        "Fixed as float   :",
        fixed_float
    )

    print()

    print(
        "Error:",
        abs(
            float_result -
            fixed_float
        )
    )
