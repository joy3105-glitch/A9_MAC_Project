import csv
from pathlib import Path
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"

with open(RESULTS / "summary_p0_p1.csv", newline="") as f:
    data = list(csv.DictReader(f))

configs = [r["config"] for r in data]

def values(key):
    return [float(r[key]) for r in data]

def save_plot(filename):
    plt.tight_layout()
    plt.savefig(RESULTS / filename, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: results/{filename}")

# 1. MAE
mae = values("mae")
plt.figure(figsize=(8, 5))
plt.plot(configs, mae, marker="o", linewidth=2)
for x, y in zip(configs, mae):
    plt.annotate(f"{y:.5f}", (x, y),
                 textcoords="offset points", xytext=(0, 9),
                 ha="center", fontsize=9)
plt.ylim(bottom=0)
plt.xlabel("Bit-width configuration")
plt.ylabel("Mean Absolute Error")
plt.title("Mean Absolute Error versus Numerical Configuration")
plt.grid(True, alpha=0.4)
save_plot("mae_vs_config.png")

# 2. RMSE
rmse = values("rmse")
plt.figure(figsize=(8, 5))
plt.plot(configs, rmse, marker="o", linewidth=2)
for x, y in zip(configs, rmse):
    plt.annotate(f"{y:.5f}", (x, y),
                 textcoords="offset points", xytext=(0, 9),
                 ha="center", fontsize=9)
plt.ylim(bottom=0)
plt.xlabel("Bit-width configuration")
plt.ylabel("Root Mean Square Error")
plt.title("Root Mean Square Error versus Numerical Configuration")
plt.grid(True, alpha=0.4)
save_plot("rmse_vs_config.png")

x = list(range(len(configs)))
width = 0.35

# 3. Generic cells
p0_cells = values("p0_cells")
p1_cells = values("p1_cells")

plt.figure(figsize=(9, 5))
bars0 = plt.bar([i-width/2 for i in x], p0_cells,
                width, label="P0")
bars1 = plt.bar([i+width/2 for i in x], p1_cells,
                width, label="P1")

plt.bar_label(bars0, padding=3, fontsize=8)
plt.bar_label(bars1, padding=3, fontsize=8)
plt.xticks(x, configs)
plt.ylim(bottom=0)
plt.xlabel("Bit-width configuration")
plt.ylabel("Generic cell count")
plt.title("Generic Logic Cell Count: P0 versus P1")
plt.legend()
plt.grid(axis="y", alpha=0.4)
save_plot("generic_cells_p0_p1.png")

# 4. Flip-flop count
p0_ff = values("p0_ff")
p1_ff = values("p1_ff")

plt.figure(figsize=(9, 5))
bars0 = plt.bar([i-width/2 for i in x], p0_ff,
                width, label="P0")
bars1 = plt.bar([i+width/2 for i in x], p1_ff,
                width, label="P1")

plt.bar_label(bars0, padding=3, fontsize=8)
plt.bar_label(bars1, padding=3, fontsize=8)
plt.xticks(x, configs)
plt.ylim(bottom=0)
plt.xlabel("Bit-width configuration")
plt.ylabel("Flip-flop count")
plt.title("Flip-Flop Count: P0 versus P1")
plt.legend()
plt.grid(axis="y", alpha=0.4)
save_plot("ff_p0_p1.png")

print("\nAll four experimental plots generated successfully.")
