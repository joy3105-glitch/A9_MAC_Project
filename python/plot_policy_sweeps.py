import csv
from pathlib import Path
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)


def read_csv(path):
    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fields = reader.fieldnames or []

    if not rows:
        raise ValueError(f"File không có dữ liệu: {path}")

    return rows, fields


def find_column(fields, candidates):
    lower_fields = {field.lower(): field for field in fields}

    for candidate in candidates:
        if candidate.lower() in lower_fields:
            return lower_fields[candidate.lower()]

    return None


def save_bar_chart(labels, values, title, ylabel, output_path):
    fig, ax = plt.subplots(figsize=(8, 5))

    bars = ax.bar(labels, values)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.set_xlabel("Configuration")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.set_axisbelow(True)

    for bar, value in zip(bars, values):
        ax.annotate(
            f"{value:.6g}",
            (bar.get_x() + bar.get_width() / 2, bar.get_height()),
            xytext=(0, 5),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    print(f"Saved: {output_path}")


def plot_rounding():
    path = RESULTS / "rounding_sweep.csv"
    rows, fields = read_csv(path)

    mode_col = find_column(fields, ["rounding_mode", "mode"])
    mae_col = find_column(fields, ["mae"])
    rmse_col = find_column(fields, ["rmse"])

    if not all([mode_col, mae_col, rmse_col]):
        raise ValueError(
            f"Không nhận diện được các cột rounding. "
            f"Các cột hiện có: {fields}"
        )

    labels = [row[mode_col] for row in rows]
    mae_values = [float(row[mae_col]) for row in rows]
    rmse_values = [float(row[rmse_col]) for row in rows]

    save_bar_chart(
        labels,
        mae_values,
        "Rounding Policy - MAE Comparison",
        "Mean Absolute Error",
        RESULTS / "rounding_mae.png",
    )

    save_bar_chart(
        labels,
        rmse_values,
        "Rounding Policy - RMSE Comparison",
        "Root Mean Square Error",
        RESULTS / "rounding_rmse.png",
    )


def plot_overflow():
    path = RESULTS / "overflow_sweep.csv"
    rows, fields = read_csv(path)

    mae_col = find_column(fields, ["mae"])
    policy_col = find_column(
        fields,
        ["overflow_mode", "policy", "mode", "overflow_policy"],
    )
    test_col = find_column(
        fields,
        ["test_type", "overflow_type", "test", "scenario", "category"],
    )

    if not mae_col or not policy_col or not test_col:
        raise ValueError(
            "Không nhận diện được cột trong overflow_sweep.csv.\n"
            f"Các cột hiện có: {fields}\n"
            "Cần xác định được cột loại kiểm thử, chính sách overflow và MAE."
        )

    groups = {}
    for row in rows:
        test_name = row[test_col]
        policy = row[policy_col]
        mae = float(row[mae_col])
        groups.setdefault(test_name, []).append((policy, mae))

    output_names = {
        "input": "input_overflow_mae.png",
        "input_overflow": "input_overflow_mae.png",
        "accumulator": "accumulator_overflow_mae.png",
        "accumulator_overflow": "accumulator_overflow_mae.png",
        "output": "output_overflow_mae.png",
        "output_overflow": "output_overflow_mae.png",
    }

    for test_name, results in groups.items():
        labels = [item[0] for item in results]
        values = [item[1] for item in results]

        normalized_name = test_name.lower().strip().replace(" ", "_")
        output_name = output_names.get(
            normalized_name,
            f"{normalized_name}_overflow_mae.png",
        )

        save_bar_chart(
            labels,
            values,
            f"Overflow Policy - {test_name} MAE Comparison",
            "Mean Absolute Error",
            RESULTS / output_name,
        )


def main():
    print("========== ROUNDING SWEEP PLOTS ==========")
    plot_rounding()

    print("\n========== OVERFLOW SWEEP PLOTS ==========")
    plot_overflow()

    print("\nAll policy sweep plots completed.")


if __name__ == "__main__":
    main()
