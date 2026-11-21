import random
import csv
from pathlib import Path

from golden_model import mac_fixed, mac_float, fixed_to_float

CONFIG = {
    "input_width": 8,
    "input_frac": 4,
    "product_width": 16,
    "product_frac": 8,
    "acc_width": 24,
    "acc_frac": 8,
    "output_width": 8,
    "output_frac": 4,
}

ROUNDING_MODES = [
    "truncate",
    "nearest_ties_away_from_zero",
]

NUM_SAMPLES = 1000
VECTOR_LENGTH = 8
INPUT_MIN = -0.75
INPUT_MAX = 0.75
RANDOM_SEED = 42


def generate_dataset():
    rng = random.Random(RANDOM_SEED)
    dataset = []

    for _ in range(NUM_SAMPLES):
        A = [rng.uniform(INPUT_MIN, INPUT_MAX)
             for _ in range(VECTOR_LENGTH)]
        B = [rng.uniform(INPUT_MIN, INPUT_MAX)
             for _ in range(VECTOR_LENGTH)]
        dataset.append((A, B))

    return dataset


def evaluate(mode, dataset):
    errors = []

    for A, B in dataset:
        reference = mac_float(A, B)

        code = mac_fixed(
            A, B,
            **CONFIG,
            rounding_mode=mode,
        )

        result = fixed_to_float(code, CONFIG["output_frac"])
        errors.append(abs(reference - result))

    mae = sum(errors) / len(errors)
    mse = sum(e * e for e in errors) / len(errors)

    return {
        "rounding_mode": mode,
        "num_samples": len(dataset),
        "mae": mae,
        "mse": mse,
        "rmse": mse ** 0.5,
        "max_error": max(errors),
    }


def main():
    dataset = generate_dataset()
    results = [evaluate(mode, dataset) for mode in ROUNDING_MODES]

    print("=" * 78)
    print("MAC ROUNDING MODE SWEEP")
    print("=" * 78)
    print(f"Samples       : {NUM_SAMPLES}")
    print(f"Vector length : {VECTOR_LENGTH}")
    print(f"Input range   : [{INPUT_MIN}, {INPUT_MAX}]")
    print(f"Random seed   : {RANDOM_SEED}")
    print()

    print(f"{'Rounding mode':<36}{'MAE':>12}{'RMSE':>12}{'Max error':>14}")
    print("-" * 78)

    for r in results:
        print(
            f"{r['rounding_mode']:<36}"
            f"{r['mae']:>12.8f}"
            f"{r['rmse']:>12.8f}"
            f"{r['max_error']:>14.8f}"
        )

    output_path = (
        Path(__file__).resolve().parent.parent
        / "results" / "rounding_sweep.csv"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)

    print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    main()
