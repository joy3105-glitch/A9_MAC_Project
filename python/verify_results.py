from golden_model import (
    mac_fixed,
    fixed_to_float,
    OUTPUT_FRAC
)


# ==========================================
# Test cases
# ==========================================

test_cases = [

    (
        [1.25],
        [1.0]
    ),

    (
        [1.25, 2.0],
        [2.0, 1.5]
    ),

    (
        [1.0, -1.0],
        [2.0, 2.0]
    ),

    (
        [3.0, 2.0, 1.0],
        [1.0, 2.0, 3.0]
    )

]


# ==========================================
# Verification
# ==========================================

print("======================================")
print("          MAC VERIFICATION")
print("======================================")


for index, (A, B) in enumerate(
    test_cases
):

    expected_fixed = mac_fixed(
        A,
        B
    )


    expected_float = fixed_to_float(
        expected_fixed,
        OUTPUT_FRAC
    )


    float_result = sum(
        a * b
        for a, b in zip(A, B)
    )


    error = abs(
        float_result -
        expected_float
    )


    print()

    print(
        f"Test {index + 1}"
    )

    print(
        "A       =",
        A
    )

    print(
        "B       =",
        B
    )

    print(
        "Expected =",
        expected_fixed
    )

    print(
        "As float =",
        expected_float
    )

    print(
        "Float    =",
        float_result
    )

    print(
        "Error    =",
        error
    )


    # Kiểm tra sai số

    if error <= 0.03125:

        print(
            "STATUS   = PASS"
        )

    else:

        print(
            "STATUS   = FAIL"
        )
