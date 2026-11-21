import csv
from pathlib import Path

from golden_model import mac_fixed, mac_float, fixed_to_float


def metrics(errors):
    mae = sum(errors) / len(errors)
    mse = sum(e * e for e in errors) / len(errors)

    return {
        "num_samples": len(errors),
        "mae": mae,
        "mse": mse,
        "rmse": mse ** 0.5,
        "max_error": max(errors),
    }


def evaluate_dataset(dataset, **kwargs):
    errors = []

    for A, B in dataset:
        reference = mac_float(A, B)

        code = mac_fixed(A, B, **kwargs)

        output_frac = kwargs["output_frac"]
        result = fixed_to_float(code, output_frac)

        errors.append(abs(reference - result))

    return metrics(errors)


def run_input_overflow():
    # Một phép nhân mỗi vector; accumulator/output đủ rộng.
    dataset = [
        ([10.0], [1.0]),
        ([-10.0], [1.0]),
        ([9.0], [-1.0]),
        ([-9.0], [-1.0]),
        ([7.0], [2.0]),
        ([-7.0], [2.0]),
    ]

    rows = []

    for mode in ["saturate", "wrap"]:
        result = evaluate_dataset(
            dataset,
            input_width=8,
            input_frac=4,
            product_width=16,
            product_frac=8,
            acc_width=24,
            acc_frac=8,
            output_width=24,
            output_frac=8,
            input_overflow_mode=mode,
        )

        rows.append({
            "experiment": "input_overflow",
            "mode": mode,
            **result,
        })

    return rows


def run_accumulator_overflow():
    # Tạo overflow ở giữa chuỗi MAC rồi cộng các tích âm.
    A = [10.0, 10.0, -10.0, -10.0]
    B = [10.0, 10.0, 10.0, 10.0]

    dataset = [(A, B)]

    rows = []

    for mode in ["saturate", "saturate_each_step", "wrap"]:
        result = evaluate_dataset(
            dataset,
            input_width=8,
            input_frac=0,
            product_width=16,
            product_frac=0,
            acc_width=8,
            acc_frac=0,
            output_width=16,
            output_frac=0,
            acc_overflow_mode=mode,
        )

        rows.append({
            "experiment": "accumulator_overflow",
            "mode": mode,
            **result,
        })

    return rows


def run_output_overflow():
    # Accumulator đủ rộng; kết quả cuối vượt miền output Q4.4.
    dataset = [
        ([7.0] * 8, [7.0] * 8),
        ([-7.0] * 8, [7.0] * 8),
        ([7.0] * 8, [-7.0] * 8),
        ([-7.0] * 8, [-7.0] * 8),
    ]

    rows = []

    for mode in ["saturate", "wrap"]:
        result = evaluate_dataset(
            dataset,
            input_width=8,
            input_frac=4,
            product_width=16,
            product_frac=8,
            acc_width=24,
            acc_frac=8,
            output_width=8,
            output_frac=4,
            output_overflow_mode=mode,
        )

        rows.append({
            "experiment": "output_overflow",
            "mode": mode,
            **result,
        })

    return rows


def main():
    results = []
    results.extend(run_input_overflow())
    results.extend(run_accumulator_overflow())
    results.extend(run_output_overflow())

    print("=" * 92)
    print("MAC OVERFLOW POLICY SWEEP")
    print("=" * 92)
    print(
        f"{'Experiment':<26}"
        f"{'Mode':<23}"
        f"{'Samples':>9}"
        f"{'MAE':>12}"
        f"{'RMSE':>12}"
        f"{'Max error':>12}"
    )
    print("-" * 92)

    for r in results:
        print(
            f"{r['experiment']:<26}"
            f"{r['mode']:<23}"
            f"{r['num_samples']:>9}"
            f"{r['mae']:>12.6f}"
            f"{r['rmse']:>12.6f}"
            f"{r['max_error']:>12.6f}"
        )

    output_path = (
        Path(__file__).resolve().parent.parent
        / "results" / "overflow_sweep.csv"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="") as f:
        fields = [
            "experiment",
            "mode",
            "num_samples",
            "mae",
            "mse",
            "rmse",
            "max_error",
        ]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)

    print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    main()
