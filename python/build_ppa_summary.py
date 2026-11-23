import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
ASIC = RESULTS / "asic_sky130_filtered"
FPGA = RESULTS / "fpga_ice40"

CLOCK_PERIOD_NS = 20.0

ARCHS = ["P0", "P1", "P2"]
CONFIGS = ["C1", "C2", "C3", "C4", "C5"]


def read_csv(path):
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def extract_timing(arch, cfg):
    path = ASIC / "timing" / f"{arch}_{cfg}_timing.log"
    text = path.read_text()

    if "========== STA COMPLETE ==========" not in text:
        raise RuntimeError(f"Incomplete STA: {path}")

    if re.search(r"(?:Error:|Warning:)", text):
        raise RuntimeError(f"STA warning/error: {path}")

    overall_match = re.search(
        r"worst slack\s+(-?\d+(?:\.\d+)?)",
        text
    )

    tns_match = re.search(
        r"\btns\s+(-?\d+(?:\.\d+)?)",
        text
    )

    section = text.split(
        "========== REG TO REG TIMING =========="
    )[-1].split(
        "========== STA COMPLETE =========="
    )[0]

    reg_match = re.search(
        r"(-?\d+(?:\.\d+)?)\s+slack\s+\((?:MET|VIOLATED)\)",
        section
    )

    if not all([overall_match, tns_match, reg_match]):
        raise RuntimeError(f"Missing timing data: {path}")

    overall_slack = float(overall_match.group(1))
    reg_slack = float(reg_match.group(1))
    tns = float(tns_match.group(1))

    reg_period = CLOCK_PERIOD_NS - reg_slack

    if reg_period <= 0:
        raise RuntimeError(f"Invalid period: {path}")

    return {
        "asic_overall_slack_ns": overall_slack,
        "asic_reg_reg_slack_ns": reg_slack,
        "asic_reg_reg_period_ns": round(reg_period, 4),
        "asic_reg_reg_fmax_est_mhz": round(
            1000.0 / reg_period, 4
        ),
        "asic_tns_ns": tns,
        "asic_timing_50mhz": (
            "PASS"
            if overall_slack >= 0 and tns >= 0
            else "FAIL"
        ),
    }


def main():
    accuracy_rows = read_csv(
        RESULTS / "bitwidth_sweep.csv"
    )

    asic_rows = read_csv(
        ASIC / "asic_sky130_summary.csv"
    )

    fpga_rows = read_csv(
        FPGA / "fpga_ice40_summary.csv"
    )

    accuracy = {
        row["name"]: row
        for row in accuracy_rows
    }

    asic = {
        (row["architecture"], row["config"]): row
        for row in asic_rows
    }

    fpga = {
        (row["architecture"], row["config"]): row
        for row in fpga_rows
    }

    if len(accuracy) != 5:
        raise RuntimeError("Expected 5 accuracy configurations")

    if len(asic) != 15 or len(fpga) != 15:
        raise RuntimeError("Expected 15 ASIC and FPGA rows")

    output_rows = []

    for arch in ARCHS:
        for cfg in CONFIGS:
            a = accuracy[cfg]
            s = asic[(arch, cfg)]
            f = fpga[(arch, cfg)]

            if (
                a["input_width"] != f["input_width"]
                or a["input_frac"] != f["input_frac"]
            ):
                raise RuntimeError(
                    f"Numeric configuration mismatch: {arch} {cfg}"
                )

            if s["check_status"] != "PASS":
                raise RuntimeError(
                    f"ASIC synthesis check failed: {arch} {cfg}"
                )

            timing = extract_timing(arch, cfg)

            row = {
                "architecture": arch,
                "config": cfg,

                "input_width": int(a["input_width"]),
                "input_frac": int(a["input_frac"]),
                "product_width": int(a["product_width"]),
                "acc_width": int(a["acc_width"]),

                "mae": float(a["mae"]),
                "mse": float(a["mse"]),
                "rmse": float(a["rmse"]),
                "max_error": float(a["max_error"]),

                "latency_cycles": int(f["latency_cycles"]),
                "ii_cycles": int(f["ii_cycles"]),

                "fpga_lut4": int(f["lut4"]),
                "fpga_ff": int(f["ff"]),
                "fpga_carry": int(f["carry"]),
                "fpga_total_cells": int(f["total_cells"]),
                "fpga_fmax_mhz": float(f["fmax_mhz"]),
                "fpga_timing_50mhz": f["timing_50mhz"],

                "asic_cell_count": int(s["cell_count"]),
                "asic_ff_count": int(s["ff_count"]),
                "asic_cell_area_um2": float(
                    s["cell_area_um2"]
                ),
                "asic_check_status": s["check_status"],
            }

            row.update(timing)
            output_rows.append(row)

    output = RESULTS / "ppa_summary.csv"

    with output.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=list(output_rows[0].keys())
        )
        writer.writeheader()
        writer.writerows(output_rows)

    print("========== PPA SUMMARY ==========")
    print("Output:", output)
    print("Rows:", len(output_rows))

    print()
    print(
        f"{'ARCH':<5} {'CFG':<5} "
        f"{'MAE':>10} "
        f"{'ASIC_AREA':>12} "
        f"{'ASIC_FMAX':>11} "
        f"{'FPGA_FMAX':>11} "
        f"{'LAT':>5}"
    )

    print("-" * 70)

    for r in output_rows:
        print(
            f"{r['architecture']:<5} "
            f"{r['config']:<5} "
            f"{r['mae']:>10.6f} "
            f"{r['asic_cell_area_um2']:>12.2f} "
            f"{r['asic_reg_reg_fmax_est_mhz']:>11.2f} "
            f"{r['fpga_fmax_mhz']:>11.2f} "
            f"{r['latency_cycles']:>5}"
        )

    print()
    print("PPA SUMMARY GENERATION: PASS")


if __name__ == "__main__":
    main()
