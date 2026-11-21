import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"

def parse_synthesis(log_path):
    text = log_path.read_text()

    cells = re.findall(r"Number of cells:\s+(\d+)", text)
    sdffe = re.findall(r"\$_SDFFE_PP0P_\s+(\d+)", text)
    sdff = re.findall(r"\$_SDFF_PP0_\s+(\d+)", text)

    if not cells or not sdffe or not sdff:
        raise ValueError(f"Cannot parse synthesis log: {log_path}")

    total_cells = int(cells[-1])
    total_ff = int(sdffe[-1]) + int(sdff[-1])

    return total_cells, total_ff

with open(RESULTS / "bitwidth_sweep.csv", newline="") as f:
    accuracy = {
        row["name"]: row
        for row in csv.DictReader(f)
    }

output = []

for config in ["C1", "C2", "C3", "C4", "C5"]:
    p0_cells, p0_ff = parse_synthesis(
        RESULTS / f"yosys_{config}.log"
    )

    p1_cells, p1_ff = parse_synthesis(
        RESULTS / f"yosys_P1_{config}.log"
    )

    row = accuracy[config]

    cell_change = p1_cells - p0_cells
    cell_change_pct = cell_change / p0_cells * 100

    stream_log = RESULTS / f"pipeline_stream_{config}.log"

    if stream_log.exists():
        stream_status = (
            "PASS" if "PIPELINE STREAMING TEST: PASS"
            in stream_log.read_text()
            else "FAIL"
        )
    else:
        stream_status = "NOT_LOGGED"

    output.append({
        "config": config,
        "input_width": row["input_width"],
        "input_frac": row["input_frac"],
        "product_width": row["product_width"],
        "acc_width": row["acc_width"],
        "mae": row["mae"],
        "rmse": row["rmse"],
        "max_error": row["max_error"],
        "p0_cells": p0_cells,
        "p1_cells": p1_cells,
        "cell_change": cell_change,
        "cell_change_percent": round(cell_change_pct, 2),
        "p0_ff": p0_ff,
        "p1_ff": p1_ff,
        "ff_increase": p1_ff - p0_ff,
        "p0_latency_cycles": 1,
        "p1_latency_cycles": 2,
        "p0_ii_cycles": 1,
        "p1_ii_cycles": 1,
        "p1_streaming_status": stream_status,
    })

output_path = RESULTS / "summary_p0_p1.csv"

with open(output_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=output[0].keys())
    writer.writeheader()
    writer.writerows(output)

print("\n========== P0/P1 EXPERIMENT SUMMARY ==========")

for r in output:
    print(f"\n{r['config']}")
    print(f"  MAE             : {float(r['mae']):.6f}")
    print(f"  RMSE            : {float(r['rmse']):.6f}")
    print(f"  Max error       : {float(r['max_error']):.6f}")
    print(f"  P0 cells        : {r['p0_cells']}")
    print(f"  P1 cells        : {r['p1_cells']}")
    print(f"  Cell change     : {r['cell_change']} ({r['cell_change_percent']}%)")
    print(f"  P0 FF           : {r['p0_ff']}")
    print(f"  P1 FF           : {r['p1_ff']}")
    print(f"  FF increase     : {r['ff_increase']}")
    print(f"  P1 streaming    : {r['p1_streaming_status']}")

print(f"\nSaved: {output_path}")
