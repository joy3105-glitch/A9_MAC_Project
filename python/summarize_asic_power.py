import csv
import math
from pathlib import Path

POWER_DIR = Path("results/asic_sky130_filtered/power")
OUTPUT = POWER_DIR / "asic_power_summary.csv"

ARCHS = ["P0", "P1", "P2"]
CONFIGS = ["C1", "C2", "C3", "C4", "C5"]

rows = []

for arch in ARCHS:
    for cfg in CONFIGS:

        log_path = POWER_DIR / f"{arch}_{cfg}_power.log"
        text = log_path.read_text()

        if "POWER COMPLETE" not in text:
            raise RuntimeError(f"Incomplete power run: {log_path}")

        total_lines = [
            line.split()
            for line in text.splitlines()
            if line.split() and line.split()[0] == "Total"
        ]

        if len(total_lines) != 1:
            raise RuntimeError(f"Invalid power report: {log_path}")

        fields = total_lines[0]

        internal, switching, leakage, total = map(
            float, fields[1:5]
        )

        values = [internal, switching, leakage, total]

        if not all(math.isfinite(v) and v >= 0 for v in values):
            raise RuntimeError(f"Invalid power values: {log_path}")

        if not math.isclose(
            internal + switching + leakage,
            total,
            rel_tol=1e-5,
            abs_tol=1e-12
        ):
            raise RuntimeError(f"Power sum mismatch: {log_path}")

        rows.append({
            "architecture": arch,
            "config": cfg,
            "clock_mhz": 50,
            "input_activity": 0.1,
            "input_duty": 0.5,
            "internal_power_mw": f"{internal * 1000:.10f}",
            "switching_power_mw": f"{switching * 1000:.10f}",
            "leakage_power_mw": f"{leakage * 1000:.10f}",
            "total_power_mw": f"{total * 1000:.10f}",
            "method": "vectorless_pre_layout"
        })

        print(
            f"{arch}-{cfg}: "
            f"Total Power = {total * 1000:.6f} mW"
        )

assert len(rows) == 15

with OUTPUT.open("w", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=list(rows[0].keys())
    )
    writer.writeheader()
    writer.writerows(rows)

print()
print(f"Total configurations: {len(rows)}")
print(f"Output: {OUTPUT}")
print("POWER SUMMARY: PASS")
