import random

from golden_model import (
    mac_fixed,
    mac_float,
    fixed_to_float,
    INPUT_WIDTH,
    INPUT_FRAC,
    OUTPUT_WIDTH,
    OUTPUT_FRAC,
    signed_range,
)

# Experiment configuration
random.seed(42)

NUM_SAMPLES = 1000
VECTOR_LENGTH = 8
INPUT_MIN = -0.75
INPUT_MAX = 0.75

errors = []
squared_errors = []

output_min_code, output_max_code = signed_range(OUTPUT_WIDTH)

boundary_hits = 0

for _ in range(NUM_SAMPLES):

    A = [
        random.uniform(INPUT_MIN, INPUT_MAX)
        for _ in range(VECTOR_LENGTH)
    ]

    B = [
        random.uniform(INPUT_MIN, INPUT_MAX)
        for _ in range(VECTOR_LENGTH)
    ]

    # Ideal floating-point result
    float_result = mac_float(A, B)

    # Fixed-point MAC result
    fixed_code = mac_fixed(A, B)
    fixed_result = fixed_to_float(fixed_code, OUTPUT_FRAC)

    # Numerical error
    error = abs(float_result - fixed_result)

    errors.append(error)
    squared_errors.append(error ** 2)

    if fixed_code in (output_min_code, output_max_code):
        boundary_hits += 1


# Calculate error metrics
mae = sum(errors) / NUM_SAMPLES
mse = sum(squared_errors) / NUM_SAMPLES
max_error = max(errors)

rmse = mse ** 0.5

# Print results
print("========================================")
print("       MAC NUMERICAL ERROR ANALYSIS")
print("========================================")

print(f"Number of samples : {NUM_SAMPLES}")
print(f"Vector length     : {VECTOR_LENGTH}")
print(f"Input range       : [{INPUT_MIN}, {INPUT_MAX}]")

print("\nError metrics")
print(f"MAE               : {mae:.8f}")
print(f"MSE               : {mse:.8f}")
print(f"RMSE              : {rmse:.8f}")
print(f"Maximum error     : {max_error:.8f}")

print("\nFixed-point configuration")
print(f"Input format      : Q{INPUT_WIDTH - INPUT_FRAC}.{INPUT_FRAC}")
print(f"Output format     : Q{OUTPUT_WIDTH - OUTPUT_FRAC}.{OUTPUT_FRAC}")
print(f"Output resolution : {1 / (2 ** OUTPUT_FRAC):.8f}")
print(f"Half resolution   : {1 / (2 ** (OUTPUT_FRAC + 1)):.8f}")

print("\nOutput boundary hits")
print(f"Boundary samples  : {boundary_hits}/{NUM_SAMPLES}")

print("\nAnalysis completed.")