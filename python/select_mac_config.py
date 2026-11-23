
import csv
from pathlib import Path

INPUT = Path(
    "results/fpga_ice40/fpga_accuracy_tradeoff.csv"
)

OUTPUT = Path(
    "results/fpga_ice40/config_selection.csv"
)

with INPUT.open(newline="") as f:
    data = list(csv.DictReader(f))

# Các kịch bản nghiên cứu, không phải yêu cầu bắt buộc
SCENARIOS = [
    {
        "name": "S1_50MHz",
        "max_mae": None,
        "min_fmax": 50.0,
        "max_lut": None,
    },
    {
        "name": "S2_MAE_0.03",
        "max_mae": 0.03,
        "min_fmax": None,
        "max_lut": None,
    },
    {
        "name": "S3_MAE_0.02",
        "max_mae": 0.02,
        "min_fmax": None,
        "max_lut": None,
    },
    {
        "name": "S4_Balanced",
        "max_mae": 0.03,
        "min_fmax": 30.0,
        "max_lut": 500,
    },
]

results = []

for scenario in SCENARIOS:
    candidates = []

    for row in data:
        mae = float(row["mae"])
        fmax = float(row["fmax_mhz"])
        lut = int(row["lut4"])

        if (
            scenario["max_mae"] is not None
            and mae > scenario["max_mae"]
        ):
            continue

        if (
            scenario["min_fmax"] is not None
            and fmax < scenario["min_fmax"]
        ):
            continue

        if (
            scenario["max_lut"] is not None
            and lut > scenario["max_lut"]
        ):
            continue

        candidates.append(row)

    # Trong số phương án hợp lệ, ưu tiên:
    # 1. Ít LUT4
    # 2. Ít FF
    # 3. Latency ít chu kỳ
    # 4. Fmax cao
    candidates.sort(
        key=lambda r: (
            int(r["lut4"]),
            int(r["ff"]),
            int(r["latency_cycles"]),
            -float(r["fmax_mhz"]),
        )
    )

    print(f"\n========== {scenario['name']} ==========")
    print(f"Valid candidates: {len(candidates)}")

    if not candidates:
        print("No feasible configuration")
        continue

    for row in candidates:
        print(
            f'{row["architecture"]}_{row["config"]} '
            f'MAE={float(row["mae"]):.6f} '
            f'LUT={row["lut4"]} '
            f'FF={row["ff"]} '
            f'Fmax={row["fmax_mhz"]} MHz'
        )

    best = candidates[0]

    results.append({
        "scenario": scenario["name"],
        "selected_architecture": best["architecture"],
        "selected_config": best["config"],
        "mae": best["mae"],
        "lut4": best["lut4"],
        "ff": best["ff"],
        "fmax_mhz": best["fmax_mhz"],
        "latency_cycles": best["latency_cycles"],
    })

    print(
        "SELECTED:",
        f'{best["architecture"]}_{best["config"]}'
    )

with OUTPUT.open("w", newline="") as f:
    fields = [
        "scenario",
        "selected_architecture",
        "selected_config",
        "mae",
        "lut4",
        "ff",
        "fmax_mhz",
        "latency_cycles",
    ]

    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(results)

print(f"\nSaved: {OUTPUT}")
