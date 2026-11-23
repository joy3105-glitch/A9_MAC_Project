
import csv
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path("results/asic_sky130_filtered")
FIG_DIR = Path("results/report_figures")
FIG_DIR.mkdir(parents=True, exist_ok=True)

ARCHS = ["P0", "P1", "P2"]
CONFIGS = ["C1", "C2", "C3", "C4", "C5"]

rows = []

for arch in ARCHS:
    for cfg in CONFIGS:
        name = f"{arch}_{cfg}"
        path = ROOT / f"{name}_check.log"

        if not path.is_file():
            raise FileNotFoundError(path)

        text = path.read_text(errors="replace")

        if "Found and reported 0 problems." not in text:
            raise RuntimeError(f"CHECK FAILED: {name}")

        cells = re.findall(r"Number of cells:\s+(\d+)", text)
        areas = re.findall(
            r"Chip area for module.*?:\s+([\d.]+)", text
        )

        if not cells or not areas:
            raise RuntimeError(f"Missing ASIC statistics: {name}")

        # Đếm FF từ bảng phân bố standard-cell.
        ff = sum(
            int(count)
            for count, cell in re.findall(
                r"^\s*(sky130_fd_sc_hd__\S+)\s+(\d+)\s*$",
                text,
                re.MULTILINE,
            )
            for cell, count in [(count, cell)]
            if cell.startswith((
                "sky130_fd_sc_hd__df",
                "sky130_fd_sc_hd__sdf",
                "sky130_fd_sc_hd__edf",
                "sky130_fd_sc_hd__sedf",
            ))
        )

        rows.append({
            "architecture": arch,
            "config": cfg,
            "cell_count": int(cells[-1]),
            "ff_count": ff,
            "cell_area_um2": float(areas[-1]),
            "check_status": "PASS",
        })

csv_path = ROOT / "asic_sky130_summary.csv"

with csv_path.open("w", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "architecture",
            "config",
            "cell_count",
            "ff_count",
            "cell_area_um2",
            "check_status",
        ],
    )
    writer.writeheader()
    writer.writerows(rows)

print("========== ASIC SKY130 SUMMARY ==========")
for row in rows:
    print(
        f"{row['architecture']}_{row['config']}: "
        f"cells={row['cell_count']:4d}, "
        f"FF={row['ff_count']:3d}, "
        f"area={row['cell_area_um2']:10.2f} um2, "
        f"{row['check_status']}"
    )

plt.figure(figsize=(9, 5.5))

for arch in ARCHS:
    subset = [r for r in rows if r["architecture"] == arch]
    plt.plot(
        [r["config"] for r in subset],
        [r["cell_area_um2"] for r in subset],
        marker="o",
        label=arch,
    )

plt.xlabel("Bit-width configuration")
plt.ylabel("Standard-cell area (um²)")
plt.title("ASIC SKY130 HD - Area vs Configuration")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()

fig_path = FIG_DIR / "asic_area_vs_config.png"
plt.savefig(fig_path, dpi=200)
plt.close()

print(f"\nSaved: {csv_path}")
print(f"Saved: {fig_path}")
