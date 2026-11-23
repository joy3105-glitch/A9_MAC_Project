#!/usr/bin/env bash
set -euo pipefail

cd "$HOME/A9_MAC_Project"

SKY130_VERILOG=$(find "$HOME/.ciel/ciel/sky130/versions" \
    -path "*/sky130A/libs.ref/sky130_fd_sc_hd/verilog" \
    -type d -print -quit)

OUT="results/asic_sky130_filtered/simulation"
mkdir -p "$OUT"

cp vectors/rtl_vectors.csv "$OUT/rtl_vectors_before_p1_sweep.csv"

trap 'cp "$OUT/rtl_vectors_before_p1_sweep.csv" vectors/rtl_vectors.csv' EXIT

for cfg in C1 C2 C3 C4 C5
do
    case "$cfg" in
        C1) IW=6;  IF=2;  AW=15; AF=4 ;;
        C2) IW=8;  IF=4;  AW=19; AF=8 ;;
        C3) IW=10; IF=6;  AW=23; AF=12 ;;
        C4) IW=12; IF=8;  AW=27; AF=16 ;;
        C5) IW=16; IF=12; AW=35; AF=24 ;;
    esac

    echo "======================================"
    echo "ASIC P1 $cfg"
    echo "======================================"

    cp "results/rtl_vectors_${cfg}.csv" vectors/rtl_vectors.csv

    iverilog -g2012 -gno-specify \
        -DFUNCTIONAL \
        -s mac_asic_p1_stream_tb \
        -Pmac_asic_p1_stream_tb.INPUT_WIDTH="$IW" \
        -Pmac_asic_p1_stream_tb.INPUT_FRAC="$IF" \
        -Pmac_asic_p1_stream_tb.ACC_WIDTH="$AW" \
        -Pmac_asic_p1_stream_tb.ACC_FRAC="$AF" \
        -Pmac_asic_p1_stream_tb.OUTPUT_WIDTH=8 \
        -Pmac_asic_p1_stream_tb.OUTPUT_FRAC=4 \
        -o "$OUT/P1_${cfg}.vvp" \
        "$SKY130_VERILOG/primitives.v" \
        "$SKY130_VERILOG/sky130_fd_sc_hd.v" \
        "results/asic_sky130_filtered/P1_${cfg}_mapped.v" \
        tb/mac_asic_p1_stream_tb.sv \
        2> "$OUT/P1_${cfg}_compile.log"

    vvp "$OUT/P1_${cfg}.vvp" > "$OUT/P1_${cfg}.log"

    grep -E \
        "Loaded vectors|Output checks|Errors|PIPELINE STREAMING TEST:" \
        "$OUT/P1_${cfg}.log"

    if ! grep -q "PIPELINE STREAMING TEST: PASS" "$OUT/P1_${cfg}.log"; then
        echo "ERROR: ASIC P1 $cfg FAILED"
        exit 1
    fi

    if ! grep -Eq "Output checks[[:space:]]*:[[:space:]]*655" "$OUT/P1_${cfg}.log"; then
        echo "ERROR: Unexpected output check count for $cfg"
        exit 1
    fi

    echo
done

echo "======================================"
echo "ASIC P1 C1-C5: ALL PASS"
echo "======================================"
