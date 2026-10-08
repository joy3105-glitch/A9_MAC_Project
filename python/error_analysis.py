import random


# ==========================================
# Fixed-point parameters
# ==========================================

INPUT_WIDTH = 8
FRAC_BITS = 4

SCALE = 2 ** FRAC_BITS

MAX_INT = 2 ** (INPUT_WIDTH - 1) - 1
MIN_INT = -2 ** (INPUT_WIDTH - 1)


# ==========================================
# Float -> Fixed
# ==========================================

def float_to_fixed(x):

    value = round(x * SCALE)

    # Saturation
    value = max(
        MIN_INT,
        min(MAX_INT, value)
    )

    return value


# ==========================================
# Fixed -> Float
# ==========================================

def fixed_to_float(x):

    return x / SCALE


# ==========================================
# Quantization error
# ==========================================

def calculate_error(x):

    fixed = float_to_fixed(x)

    recovered = fixed_to_float(fixed)

    return x - recovered


# ==========================================
# Generate random samples
# ==========================================

random.seed(42)

N = 1000

errors = []


for _ in range(N):

    x = random.uniform(-7.9, 7.9)

    error = calculate_error(x)

    errors.append(error)


# ==========================================
# Error metrics
# ==========================================

mae = sum(
    abs(e) for e in errors
) / N


mse = sum(
    e ** 2 for e in errors
) / N


max_error = max(
    abs(e) for e in errors
)


# ==========================================
# Print results
# ==========================================

print("================================")
print("     QUANTIZATION ERROR")
print("================================")

print()

print(
    f"Number of samples : {N}"
)

print(
    f"MAE               : {mae:.8f}"
)

print(
    f"MSE               : {mse:.8f}"
)

print(
    f"Maximum error     : {max_error:.8f}"
)

print()

print("Q4.4 resolution:")

print(
    1 / SCALE
)

print()

print("Theoretical rounding error:")

print(
    1 / (2 * SCALE)
)
