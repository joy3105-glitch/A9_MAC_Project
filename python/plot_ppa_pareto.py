import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
PLOTS = RESULTS / "ppa_plots"
PLOTS.mkdir(parents=True, exist_ok=True)

with (RESULTS / "ppa_summary.csv").open(newline="") as f:
    rows = list(csv.DictReader(f))

assert len(rows) == 15, "Expected 15 PPA configurations"

for r in rows:
    for key in [
        "mae",
        "asic_cell_area_um2",
        "asic_reg_reg_fmax_est_mhz",
        "fpga_fmax_mhz",
        "asic_total_power_mw",
    ]:
        r[key] = float(r[key])

ARCHS = ["P0", "P1", "P2"]
CONFIGS = ["C1", "C2", "C3", "C4", "C5"]

MARKERS = {"P0": "o", "P1": "s", "P2": "^"}


def get_rows(arch):
    return sorted(
        [r for r in rows if r["architecture"] == arch],
        key=lambda r: int(r["config"][1:])
    )


def save_plot(filename):
    plt.tight_layout()
    plt.savefig(PLOTS / filename, dpi=200)
    plt.close()
    print("Saved:", PLOTS / filename)


# 1. Accuracy vs bit-width
p0 = get_rows("P0")

plt.figure(figsize=(7, 4.5))
plt.plot(
    [r["input_width"] for r in p0],
    [r["mae"] for r in p0],
    marker="o"
)
plt.xlabel("Input width (bits)")
plt.ylabel("Mean Absolute Error")
plt.title("Accuracy vs Input Bit-width")
plt.grid(alpha=0.3)
save_plot("accuracy_vs_bitwidth.png")


# 2. ASIC area vs MAE
plt.figure(figsize=(7, 5))

for arch in ARCHS:
    data = get_rows(arch)
    plt.plot(
        [r["asic_cell_area_um2"] for r in data],
        [r["mae"] for r in data],
        marker=MARKERS[arch],
        label=arch
    )

plt.xlabel("ASIC standard-cell area (um2)")
plt.ylabel("MAE")
plt.title("ASIC Area vs Accuracy")
plt.legend()
plt.grid(alpha=0.3)
save_plot("asic_area_vs_mae.png")


# 3. ASIC Fmax vs area
plt.figure(figsize=(7, 5))

for arch in ARCHS:
    data = get_rows(arch)
    plt.plot(
        [r["asic_cell_area_um2"] for r in data],
        [r["asic_reg_reg_fmax_est_mhz"] for r in data],
        marker=MARKERS[arch],
        label=arch
    )

plt.xlabel("ASIC standard-cell area (um2)")
plt.ylabel("Estimated reg-to-reg Fmax (MHz)")
plt.title("ASIC Area vs Estimated Fmax")
plt.legend()
plt.grid(alpha=0.3)
save_plot("asic_area_vs_fmax.png")


# 4. FPGA vs ASIC Fmax
plt.figure(figsize=(7, 5))

for arch in ARCHS:
    data = get_rows(arch)
    plt.plot(
        [r["fpga_fmax_mhz"] for r in data],
        [r["asic_reg_reg_fmax_est_mhz"] for r in data],
        marker=MARKERS[arch],
        label=arch
    )

plt.xlabel("FPGA Fmax (MHz)")
plt.ylabel("ASIC estimated reg-to-reg Fmax (MHz)")
plt.title("FPGA vs ASIC Timing")
plt.legend()
plt.grid(alpha=0.3)
save_plot("fpga_vs_asic_fmax.png")


# 5. Pareto dominance: MAE min, area min, power min, Fmax max
def dominates(a, b):
    not_worse = (
        a["mae"] <= b["mae"]
        and a["asic_cell_area_um2"] <= b["asic_cell_area_um2"]
        and a["asic_reg_reg_fmax_est_mhz"]
            >= b["asic_reg_reg_fmax_est_mhz"]
        and a["asic_total_power_mw"] <= b["asic_total_power_mw"]
    )

    strictly_better = (
        a["mae"] < b["mae"]
        or a["asic_cell_area_um2"] < b["asic_cell_area_um2"]
        or a["asic_reg_reg_fmax_est_mhz"]
            > b["asic_reg_reg_fmax_est_mhz"]
        or a["asic_total_power_mw"] < b["asic_total_power_mw"]
    )

    return not_worse and strictly_better


for r in rows:
    r["pareto"] = not any(
        dominates(other, r)
        for other in rows
        if other is not r
    )


# Export Pareto results
out = RESULTS / "asic_pareto_summary.csv"

with out.open("w", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "architecture",
            "config",
            "mae",
            "asic_cell_area_um2",
            "asic_reg_reg_fmax_est_mhz",
            "asic_total_power_mw",
            "pareto",
        ]
    )
    writer.writeheader()

    for r in rows:
        writer.writerow({
            "architecture": r["architecture"],
            "config": r["config"],
            "mae": r["mae"],
            "asic_cell_area_um2": r["asic_cell_area_um2"],
            "asic_reg_reg_fmax_est_mhz":
                r["asic_reg_reg_fmax_est_mhz"],
            "asic_total_power_mw": r["asic_total_power_mw"],
            "pareto": r["pareto"],
        })


# 6. Pareto visualization
plt.figure(figsize=(8, 5.5))

for arch in ARCHS:
    data = get_rows(arch)

    plt.scatter(
        [r["asic_cell_area_um2"] for r in data],
        [r["asic_reg_reg_fmax_est_mhz"] for r in data],
        marker=MARKERS[arch],
        label=arch
    )

for r in rows:
    if r["pareto"]:
        plt.annotate(
            f"{r['architecture']}-{r['config']}",
            (
                r["asic_cell_area_um2"],
                r["asic_reg_reg_fmax_est_mhz"]
            ),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=8
        )

plt.xlabel("ASIC standard-cell area (um2)")
plt.ylabel("Estimated reg-to-reg Fmax (MHz)")
plt.title("ASIC Pareto Candidates (MAE, Area, Power, Fmax)")
plt.legend()
plt.grid(alpha=0.3)
save_plot("asic_pareto_candidates.png")


print("\n========== ASIC PARETO FRONTIER ==========")

pareto_rows = [r for r in rows if r["pareto"]]

for r in pareto_rows:
    print(
        f"{r['architecture']}-{r['config']}: "
        f"MAE={r['mae']:.6f}, "
        f"Area={r['asic_cell_area_um2']:.2f} um2, "
        f"Fmax={r['asic_reg_reg_fmax_est_mhz']:.2f} MHz, "
        f"Power={r['asic_total_power_mw']:.6f} mW"
    )

print(f"\nPareto candidates: {len(pareto_rows)}/15")
print("PPA PLOTS AND PARETO: PASS")


# 7. ASIC power vs input bit-width
plt.figure(figsize=(7, 5))

for arch in ARCHS:
    data = get_rows(arch)

    plt.plot(
        [int(r["input_width"]) for r in data],
        [r["asic_total_power_mw"] for r in data],
        marker=MARKERS[arch],
        label=arch
    )

plt.xlabel("Input width (bits)")
plt.ylabel("Estimated total power (mW)")
plt.title("ASIC Power vs Input Bit-width at 50 MHz")
plt.legend()
plt.grid(alpha=0.3)
save_plot("asic_power_vs_bitwidth.png")


# 8. ASIC power vs numerical error
plt.figure(figsize=(7, 5))

for arch in ARCHS:
    data = get_rows(arch)

    plt.plot(
        [r["asic_total_power_mw"] for r in data],
        [r["mae"] for r in data],
        marker=MARKERS[arch],
        label=arch
    )

plt.xlabel("Estimated total power (mW)")
plt.ylabel("MAE")
plt.title("ASIC Power vs Accuracy")
plt.legend()
plt.grid(alpha=0.3)
save_plot("asic_power_vs_mae.png")


# 9. ASIC power vs area
plt.figure(figsize=(7, 5))

for arch in ARCHS:
    data = get_rows(arch)

    plt.plot(
        [r["asic_cell_area_um2"] for r in data],
        [r["asic_total_power_mw"] for r in data],
        marker=MARKERS[arch],
        label=arch
    )

plt.xlabel("ASIC standard-cell area (um2)")
plt.ylabel("Estimated total power (mW)")
plt.title("ASIC Area vs Power at 50 MHz")
plt.legend()
plt.grid(alpha=0.3)
save_plot("asic_power_vs_area.png")

print("ASIC POWER PLOTS: PASS")
