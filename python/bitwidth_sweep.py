import random
import csv
from pathlib import Path

from golden_model import mac_fixed, mac_float, fixed_to_float


# Các cấu hình khảo sát
CONFIGS = [
    {"name": "C1", "input_width": 6,  "input_frac": 2},
    {"name": "C2", "input_width": 8,  "input_frac": 4},
    {"name": "C3", "input_width": 10, "input_frac": 6},
    {"name": "C4", "input_width": 12, "input_frac": 8},
    {"name": "C5", "input_width": 16, "input_frac": 12},
]

# Thông số dữ liệu thử nghiệm
NUM_SAMPLES = 1000
VECTOR_LENGTH = 8
INPUT_MIN = -0.75
INPUT_MAX = 0.75
RANDOM_SEED = 42

# Giữ nguyên định dạng đầu ra để so sánh công bằng
OUTPUT_WIDTH = 8
OUTPUT_FRAC = 4


def generate_dataset():
    """Tạo một bộ dữ liệu cố định dùng chung cho mọi cấu hình."""
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
    """Đánh giá sai số của một cấu hình MAC."""
    input_width = config["input_width"]
    input_frac = config["input_frac"]

    product_width = 2 * input_width
    product_frac = 2 * input_frac

    # Thêm 3 bit dự phòng cho accumulator
    acc_width = product_width + 3
    acc_frac = product_frac

    errors = []

    for A, B in dataset:
        reference = mac_float(A, B)

        output_code = mac_fixed(
            A,
            B,
            input_width=input_width,
            input_frac=input_frac,
            product_width=product_width,
            product_frac=product_frac,
            acc_width=acc_width,
            acc_frac=acc_frac,
            output_width=OUTPUT_WIDTH,
            output_frac=OUTPUT_FRAC,
        )

        fixed_result = fixed_to_float(output_code, OUTPUT_FRAC)
        errors.append(abs(reference - fixed_result))

    mae = sum(errors) / len(errors)
    mse = sum(error ** 2 for error in errors) / len(errors)
    rmse = mse ** 0.5
    max_error = max(errors)

    return {
        "name": config["name"],
        "input_width": input_width,
        "input_frac": input_frac,
        "product_width": product_width,
        "acc_width": acc_width,
        "mae": mae,
        "mse": mse,
        "rmse": rmse,
        "max_error": max_error,
    }


def main():
    dataset = generate_dataset()
    results = []

    print("=" * 75)
    print("          MAC BIT-WIDTH SWEEP EXPERIMENT")
    print("=" * 75)

    print(f"Number of samples : {NUM_SAMPLES}")
    print(f"Vector length     : {VECTOR_LENGTH}")
    print(f"Input range       : [{INPUT_MIN}, {INPUT_MAX}]")
    print(f"Random seed       : {RANDOM_SEED}")
    print(f"Output format     : Q{OUTPUT_WIDTH - OUTPUT_FRAC}.{OUTPUT_FRAC}")

    for config in CONFIGS:
        result = evaluate_config(config, dataset)
        results.append(result)

    print("\nRESULTS")
    print("-" * 75)
    print(
        f"{'Config':<8}"
        f"{'Input':<12}"
        f"{'Product':<10}"
        f"{'ACC':<8}"
        f"{'MAE':<14}"
        f"{'RMSE':<14}"
        f"{'Max Error':<14}"
    )
    print("-" * 75)

    for result in results:
        input_format = (
            f"{result['input_width']}b/{result['input_frac']}f"
        )

        print(
            f"{result['name']:<8}"
            f"{input_format:<12}"
            f"{result['product_width']:<10}"
            f"{result['acc_width']:<8}"
            f"{result['mae']:<14.8f}"
            f"{result['rmse']:<14.8f}"
            f"{result['max_error']:<14.8f}"
        )

    # Lưu kết quả để sử dụng trong báo cáo
    output_path = Path(__file__).resolve().parent.parent
    output_path = output_path / "results" / "bitwidth_sweep.csv"

    with output_path.open("w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "name",
                "input_width",
                "input_frac",
                "product_width",
                "acc_width",
                "mae",
                "mse",
                "rmse",
                "max_error",
            ],
        )
        writer.writeheader()
        writer.writerows(results)

    print("\nExperiment completed.")
    print(f"Results saved to: {output_path}")


if __name__ == "__main__":
    main()
