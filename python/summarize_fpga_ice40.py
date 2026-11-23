
import csv
import json
import re
from collections import Counter
from pathlib import Path

OUT = Path("results/fpga_ice40")

ARCHS = {
    "P0": ("mac_parameterized", 1),
    "P1": ("mac_pipeline", 2),
    "P2": ("mac_pipeline2", 3),
}

CONFIGS = {
    "C1": (6, 2),
    "C2": (8, 4),
    "C3": (10, 6),
    "C4": (12, 8),
    "C5": (16, 12),
}

rows = []
errors = []

for arch, (top, latency) in ARCHS.items():
    for config, (width, frac) in CONFIGS.items():
        name = f"{arch}_{config}"

        json_path = OUT / f"{name}.json"
        log_path = OUT / f"{name}_nextpnr.log"
        asc_path = OUT / f"{name}.asc"

        if not all(p.is_file() for p in
                   (json_path, log_path, asc_path)):
            errors.append(f"{name}: missing file")
            continue

        try:
            design = json.loads(json_path.read_text())
            cells = design["modules"][top]["cells"]

            counts = Counter(
                cell["type"] for cell in cells.values()
            )

            lut = counts["SB_LUT4"]
            ff = sum(
                n for cell_type, n in counts.items()
                if cell_type.startswith("SB_DFF")
            )
            carry = counts["SB_CARRY"]
            total = sum(counts.values())

            log = log_path.read_text(errors="replace")

            matches = re.findall(
                r"Max frequency for clock.*?:\s*"
                r"([0-9.]+)\s*MHz",
                log
            )

            if not matches:
                raise ValueError("Fmax not found")

            if "Program finished normally." not in log:
                raise ValueError("nextpnr did not finish normally")

            fmax = float(matches[-1])

            rows.append({
                "architecture": arch,
                "config": config,
                "input_width": width,
                "input_frac": frac,
                "lut4": lut,
                "ff": ff,
                "carry": carry,
                "total_cells": total,
                "latency_cycles": latency,
                "ii_cycles": 1,
                "fmax_mhz": fmax,
                "timing_50mhz": (
                    "PASS" if fmax >= 50 else "FAIL"
                ),
            })

            print(
                f"{name:6s} "
                f"LUT={lut:5d} "
                f"FF={ff:4d} "
                f"Carry={carry:4d} "
                f"Fmax={fmax:6.2f} MHz"
            )

        except (ValueError, KeyError, OSError) as exc:
            errors.append(f"{name}: {exc}")

if errors:
    print("\nERRORS:")
    for error in errors:
        print(" -", error)
    raise SystemExit(1)

if len(rows) != 15:
    raise SystemExit(
        f"Expected 15 results, found {len(rows)}"
    )

output = OUT / "fpga_ice40_summary.csv"

with output.open("w", newline="") as file:
    writer = csv.DictWriter(
        file, fieldnames=list(rows[0].keys())
    )
    writer.writeheader()
    writer.writerows(rows)

print(f"\nSUCCESS: {len(rows)} configurations")
print(f"Saved: {output}")
