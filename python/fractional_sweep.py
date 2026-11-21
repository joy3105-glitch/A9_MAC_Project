import random
import csv
from pathlib import Path

from golden_model import mac_fixed, mac_float, fixed_to_float

# Giữ cố định tổng độ rộng đầu vào
INPUT_WIDTH = 8

# Khảo sát phân bổ fractional bits
CONFIGS = [
    {"name": "F1", "input_frac": 2},
    {"name": "F2", "input_frac": 3},
    {"name": "F3", "input_frac": 4},
    {"name": "F4", "input_frac": 5},
    {"name": "F5", "input_frac": 6},
]

# Accumulator cố định
ACC_WIDTH = 24
ACC_FRAC = 8

# Output cố định
OUTPUT_WIDTH = 8
OUTPUT_FRAC = 4

# Dataset cố định, giống bitwidth_sweep.py
NUM_SAMPLES = 1000
VECTOR_LENGTH = 8
INPUT_MIN = -0.75
INPUT_MAX = 0.75
RANDOM_SEED = 42


def generate_dataset():
    rng = random.Random(RANDOM_SEED)
    dataset = []

    for _ in range(NUM_SAMPLES):
        A = [
            rng.uniform(INPUT_MIN, INPUT_MAX)
            for _ in range(VECTOR_LENGTH)
        ]

        B = [
            rng.uniform(INPUT_MIN, INPUT_MAX)
            for _ in range(VECTOR_LENGTH)
        ]

        dataset.append((A, B))

    return dataset


def evaluate_config(config, dataset):
    input_frac = config["input_frac"]

    product_width = 2 * INPUT_WIDTH
    product_frac = 2 * input_frac

    errors = []

    for A, B in dataset:
        reference = mac_float(A, B)

        output_code = mac_fixed(
            A,
            B,
            input_width=INPUT_WIDTH,
            input_frac=input_frac,
            product_width=product_width,
            product_frac=product_frac,
            acc_width=ACC_WIDTH,
            acc_frac=ACC_FRAC,
            output_width=OUTPUT_WIDTH,
            output_frac=OUTPUT_FRAC,
        )

        fixed_result = fixed_to_float(
            output_code,
            OUTPUT_FRAC
        )

        errors.append(abs(reference - fixed_result))

    mae = sum(errors) / len(errors)
    mse = sum(error ** 2 for error in errors) / len(errors)
    rmse = mse ** 0.5
    max_error = max(errors)

    return {
        "name": config["name"],
        "input_width": INPUT_WIDTH,
        "input_frac": input_frac,
        "product_width": product_width,
        "product_frac": product_frac,
        "acc_width": ACC_WIDTH,
        "acc_frac": ACC_FRAC,
        "mae": mae,
        "mse": mse,
        "rmse": rmse,
        "max_error": max_error,
    }


def main():
    dataset = generate_dataset()
    results = []

    print("=" * 85)
    print("          MAC FRACTIONAL-BIT ALLOCATION SWEEP")
    print("=" * 85)

    print(f"Number of samples : {NUM_SAMPLES}")
    print(f"Vector length     : {VECTOR_LENGTH}")
    print(f"Input range       : [{INPUT_MIN}, {INPUT_MAX}]")
    print(f"Random seed       : {RANDOM_SEED}")
    print(f"Input width       : {INPUT_WIDTH}")
    print(f"Accumulator       : {ACC_WIDTH} bits, {ACC_FRAC} frac")
    print(f"Output            : {OUTPUT_WIDTH} bits, {OUTPUT_FRAC} frac")

    for config in CONFIGS:
        results.append(evaluate_config(config, dataset))

    print("\nRESULTS")
    print("-" * 85)
    print(
        f"{'Config':<9}"
        f"{'Input':<12}"
        f"{'Product':<13}"
        f"{'MAE':<14}"
        f"{'RMSE':<14}"
        f"{'Max Error':<14}"
    )
    print("-" * 85)

    for r in results:
        input_format = f"{r['input_width']}b/{r['input_frac']}f"
        product_format = f"{r['product_width']}b/{r['product_frac']}f"

        print(
            f"{r['name']:<9}"
            f"{input_format:<12}"
            f"{product_format:<13}"
            f"{r['mae']:<14.8f}"
            f"{r['rmse']:<14.8f}"
            f"{r['max_error']:<14.8f}"
        )

    output_path = (
        Path(__file__).resolve().parent.parent
        / "results"
        / "fractional_sweep.csv"
    )

    with output_path.open("w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(results[0].keys())
        )
        writer.writeheader()
        writer.writerows(results)

    print("\nExperiment completed.")
    print(f"Results saved to: {output_path}")


if __name__ == "__main__":
    main()
