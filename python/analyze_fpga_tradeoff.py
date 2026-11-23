
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path("results")
FPGA = ROOT / "fpga_ice40"
FIG = ROOT / "report_figures"
FIG.mkdir(parents=True, exist_ok=True)


def load_csv(path):
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


accuracy_rows = load_csv(ROOT / "bitwidth_sweep.csv")
fpga_rows = load_csv(FPGA / "fpga_ice40_summary.csv")

accuracy = {r["name"]: r for r in accuracy_rows}

results = []

for hw in fpga_rows:
    config = hw["config"]
    acc = accuracy[config]

    # Kiểm tra dữ liệu được ghép đúng cấu hình
    assert int(hw["input_width"]) == int(acc["input_width"])
    assert int(hw["input_frac"]) == int(acc["input_frac"])

    fmax = float(hw["fmax_mhz"])
    latency = int(hw["latency_cycles"])
    ii = int(hw["ii_cycles"])

    results.append({
        "architecture": hw["architecture"],
        "config": config,
        "input_width": int(hw["input_width"]),
        "input_frac": int(hw["input_frac"]),
        "mae": float(acc["mae"]),
        "rmse": float(acc["rmse"]),
        "max_error": float(acc["max_error"]),
        "lut4": int(hw["lut4"]),
        "ff": int(hw["ff"]),
        "carry": int(hw["carry"]),
        "fmax_mhz": fmax,
        "latency_cycles": latency,
        "latency_ns": 1000 * latency / fmax,
        "ii_cycles": ii,
        "throughput_mmac_s": fmax / ii,
        "timing_50mhz": hw["timing_50mhz"],
    })


# Pareto: MAE, LUT4, FF, latency thấp hơn là tốt;
# Fmax cao hơn là tốt.
# Carry cells được báo cáo riêng, không dùng trong
# Pareto chính để tránh gộp tài nguyên khác loại.
MIN_KEYS = [
    "mae", "lut4", "ff", "latency_cycles"
]
MAX_KEYS = ["fmax_mhz"]


def dominates(a, b):
    no_worse = (
        all(a[k] <= b[k] for k in MIN_KEYS)
        and all(a[k] >= b[k] for k in MAX_KEYS)
    )

    strictly_better = (
        any(a[k] < b[k] for k in MIN_KEYS)
        or any(a[k] > b[k] for k in MAX_KEYS)
    )

    return no_worse and strictly_better


for row in results:
    row["pareto"] = "YES" if not any(
        dominates(other, row)
        for other in results
        if other is not row
    ) else "NO"


output = FPGA / "fpga_accuracy_tradeoff.csv"

with output.open("w", newline="") as f:
    writer = csv.DictWriter(
        f, fieldnames=list(results[0].keys())
    )
    writer.writeheader()
    writer.writerows(results)


# Biểu đồ MAE và LUT4, chia theo kiến trúc
plt.figure(figsize=(9, 6))

for arch, marker in [
    ("P0", "o"), ("P1", "s"), ("P2", "^")
]:
    subset = [
        r for r in results
        if r["architecture"] == arch
    ]

    plt.plot(
        [r["lut4"] for r in subset],
        [r["mae"] for r in subset],
        marker=marker,
        label=arch
    )

    for r in subset:
        plt.annotate(
            r["config"],
            (r["lut4"], r["mae"]),
            xytext=(4, 4),
            textcoords="offset points",
            fontsize=8
        )

plt.xlabel("FPGA LUT4")
plt.ylabel("Mean Absolute Error (MAE)")
plt.title("Accuracy vs FPGA LUT4")
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig(
    FIG / "fpga_mae_vs_lut4.png",
    dpi=200
)
plt.close()


# Biểu đồ Fmax
plt.figure(figsize=(9, 6))

for arch in ["P0", "P1", "P2"]:
    subset = [
        r for r in results
        if r["architecture"] == arch
    ]

    plt.plot(
        [r["config"] for r in subset],
        [r["fmax_mhz"] for r in subset],
        marker="o",
        label=arch
    )

plt.axhline(
    50, linestyle="--",
    label="50 MHz target"
)
plt.xlabel("Bit-width configuration")
plt.ylabel("Fmax (MHz)")
plt.title("FPGA Fmax vs Configuration")
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig(
    FIG / "fpga_fmax_vs_config.png",
    dpi=200
)
plt.close()


print("========== TRADE-OFF SUMMARY ==========")

for r in results:
    print(
        f'{r["architecture"]}_{r["config"]} '
        f'MAE={r["mae"]:.6f} '
        f'LUT={r["lut4"]:4d} '
        f'FF={r["ff"]:3d} '
        f'Fmax={r["fmax_mhz"]:6.2f} '
        f'Latency={r["latency_ns"]:7.2f}ns '
        f'Pareto={r["pareto"]}'
    )

print("\n========== PARETO CONFIGURATIONS ==========")
for r in results:
    if r["pareto"] == "YES":
        print(f'{r["architecture"]}_{r["config"]}')

print(f"\nSaved: {output}")
print(f"Figures: {FIG}")
