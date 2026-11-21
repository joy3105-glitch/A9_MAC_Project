import csv
from pathlib import Path
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
CSV_FILE = ROOT / "results" / "fractional_sweep.csv"
OUT_DIR = ROOT / "results"

with open(CSV_FILE, newline="") as f:
    rows = list(csv.DictReader(f))

configs = [r["name"] for r in rows]
frac_bits = [int(r["input_frac"]) for r in rows]

metrics = [
    ("mae", "Mean Absolute Error vs Fractional Bits",
     "MAE", "mae_vs_fractional_bits.png"),
    ("rmse", "Root Mean Square Error vs Fractional Bits",
     "RMSE", "rmse_vs_fractional_bits.png"),
    ("max_error", "Maximum Error vs Fractional Bits",
     "Maximum Error", "max_error_vs_fractional_bits.png"),
]

for key, title, ylabel, filename in metrics:
    values = [float(r[key]) for r in rows]

    plt.figure(figsize=(8, 5))
    plt.plot(frac_bits, values, marker="o", linewidth=2)

    for x, y, name in zip(frac_bits, values, configs):
        plt.annotate(
            f"{name}: {y:.5f}",
            (x, y),
            textcoords="offset points",
            xytext=(0, 9),
            ha="center",
            fontsize=8
        )

    plt.title(title)
    plt.xlabel("Input Fractional Bits")
    plt.ylabel(ylabel)
    plt.xticks(frac_bits)
    plt.ylim(bottom=0)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUT_DIR / filename, dpi=300)
    plt.close()

print("Fractional sweep plots generated:")
for _, _, _, filename in metrics:
    print(OUT_DIR / filename)
