import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"

MAE_LIMIT = 0.02

with (RESULTS / "ppa_summary.csv").open(newline="") as f:
    rows = list(csv.DictReader(f))

assert len(rows) == 15

for r in rows:
    for key in [
        "mae",
        "rmse",
        "asic_cell_area_um2",
        "asic_total_power_mw",
        "asic_reg_reg_fmax_est_mhz",
        "fpga_fmax_mhz",
    ]:
        r[key] = float(r[key])

    r["latency_cycles"] = int(r["latency_cycles"])
    r["ii_cycles"] = int(r["ii_cycles"])

    r["asic_throughput_est_mmac_s"] = (
        r["asic_reg_reg_fmax_est_mhz"] / r["ii_cycles"]
    )

    r["fpga_throughput_mmac_s"] = (
        r["fpga_fmax_mhz"] / r["ii_cycles"]
    )

eligible = [
    r for r in rows
    if r["mae"] <= MAE_LIMIT
]

assert eligible, "No configuration meets MAE limit"

criteria = [
    (
        "minimum_asic_area",
        "asic_cell_area_um2",
        min
    ),
    (
        "minimum_asic_power",
        "asic_total_power_mw",
        min
    ),
    (
        "maximum_asic_fmax",
        "asic_reg_reg_fmax_est_mhz",
        max
    ),
    (
        "maximum_fpga_fmax",
        "fpga_fmax_mhz",
        max
    ),
    (
        "minimum_latency_cycles",
        "latency_cycles",
        min
    ),
    (
        "minimum_mae",
        "mae",
        min
    ),
]

selected = []

print("========== OPTIMIZATION RECOMMENDATION ==========")
print(f"MAE limit: {MAE_LIMIT}")
print(f"Eligible configurations: {len(eligible)}/15")
print()

for objective, metric, selector in criteria:

    best = selector(r[metric] for r in eligible)

    for r in eligible:
        if r[metric] != best:
            continue

        selected.append({
            "objective": objective,
            "mae_limit": MAE_LIMIT,
            "architecture": r["architecture"],
            "config": r["config"],
            "mae": r["mae"],
            "asic_cell_area_um2": r["asic_cell_area_um2"],
            "asic_total_power_mw": r["asic_total_power_mw"],
            "asic_reg_reg_fmax_est_mhz":
                r["asic_reg_reg_fmax_est_mhz"],
            "fpga_fmax_mhz": r["fpga_fmax_mhz"],
            "latency_cycles": r["latency_cycles"],
            "ii_cycles": r["ii_cycles"],
            "asic_throughput_est_mmac_s":
                r["asic_throughput_est_mmac_s"],
            "fpga_throughput_mmac_s":
                r["fpga_throughput_mmac_s"],
        })

        print(
            f"{objective:25s}: "
            f"{r['architecture']}-{r['config']} "
            f"({metric}={best:.6f})"
        )

output = RESULTS / "optimization_recommendation.csv"

with output.open("w", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=list(selected[0].keys())
    )
    writer.writeheader()
    writer.writerows(selected)

print()
print("Output:", output)
print("OPTIMIZATION RECOMMENDATION: PASS")
