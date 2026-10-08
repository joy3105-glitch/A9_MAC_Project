# ==========================================
# A9 MAC NUMERIC SPECIFICATION
# ==========================================

INPUT_WIDTH = 8
INPUT_FRAC = 4

PRODUCT_WIDTH = 16
PRODUCT_FRAC = 8

ACC_WIDTH = 24
ACC_FRAC = 8

OUTPUT_WIDTH = 8
OUTPUT_FRAC = 4


def signed_range(bits):
    """
    Trả về khoảng giá trị nguyên của signed fixed-width.
    """

    minimum = -(2 ** (bits - 1))

    maximum = 2 ** (bits - 1) - 1

    return minimum, maximum


print("======================================")
print("       A9 MAC NUMERIC SPECIFICATION")
print("======================================")

print()

print(
    f"Input width       : {INPUT_WIDTH} bits"
)

print(
    f"Input format      : "
    f"Q{INPUT_WIDTH - INPUT_FRAC}.{INPUT_FRAC}"
)

print()

print(
    f"Product width     : {PRODUCT_WIDTH} bits"
)

print(
    f"Product format    : "
    f"Q{PRODUCT_WIDTH - PRODUCT_FRAC}.{PRODUCT_FRAC}"
)

print()

print(
    f"Accumulator width : {ACC_WIDTH} bits"
)

print(
    f"Accumulator format: "
    f"Q{ACC_WIDTH - ACC_FRAC}.{ACC_FRAC}"
)

print()

print(
    f"Output width      : {OUTPUT_WIDTH} bits"
)

print(
    f"Output format     : "
    f"Q{OUTPUT_WIDTH - OUTPUT_FRAC}.{OUTPUT_FRAC}"
)

print()

print("Signed integer ranges")
print("-----------------------------")


for name, bits in [
    ("Input", INPUT_WIDTH),
    ("Product", PRODUCT_WIDTH),
    ("Accumulator", ACC_WIDTH),
    ("Output", OUTPUT_WIDTH)
]:

    minimum, maximum = signed_range(bits)

    print(
        f"{name:12}: "
        f"{minimum:8d} -> {maximum:8d}"
    )
