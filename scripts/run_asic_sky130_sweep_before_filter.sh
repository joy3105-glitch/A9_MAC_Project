
#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

LIB=$(find "$HOME/.ciel/ciel/sky130/versions" \
    -path "*/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib" \
    -type f -print -quit)

if [[ -z "$LIB" || ! -s "$LIB" ]]; then
    echo "ERROR: SKY130 HD Liberty not found"
    exit 1
fi

OUT="results/asic_sky130"
mkdir -p "$OUT"

ARCHS=("P0" "P1" "P2")

CONFIGS=("C1" "C2" "C3" "C4" "C5")
INPUT_WIDTHS=(6 8 10 12 16)
INPUT_FRACS=(2 4 6 8 12)
ACC_WIDTHS=(15 19 23 27 35)
ACC_FRACS=(4 8 12 16 24)

for arch in "${ARCHS[@]}"; do

    case "$arch" in
        P0)
            RTL="rtl/mac_parameterized.sv"
            TOP="mac_parameterized"
            ;;
        P1)
            RTL="rtl/mac_pipeline.sv"
            TOP="mac_pipeline"
            ;;
        P2)
            RTL="rtl/mac_pipeline2.sv"
            TOP="mac_pipeline2"
            ;;
    esac

    for i in "${!CONFIGS[@]}"; do

        cfg="${CONFIGS[$i]}"
        name="${arch}_${cfg}"

        echo "========== ASIC $name =========="

        log="$OUT/${name}.log"
        netlist="$OUT/${name}_mapped.v"
        checklog="$OUT/${name}_check.log"

        yosys -Q -T -l "$log" -p "
            read_verilog -sv $RTL

            hierarchy -check -top $TOP \
                -chparam INPUT_WIDTH ${INPUT_WIDTHS[$i]} \
                -chparam INPUT_FRAC ${INPUT_FRACS[$i]} \
                -chparam ACC_WIDTH ${ACC_WIDTHS[$i]} \
                -chparam ACC_FRAC ${ACC_FRACS[$i]} \
                -chparam OUTPUT_WIDTH 8 \
                -chparam OUTPUT_FRAC 4

            synth -top $TOP -noabc
            dfflibmap -liberty $LIB
            abc -liberty $LIB
            clean
            stat -liberty $LIB

            write_verilog -noattr -noexpr $netlist
        " > /dev/null

        # Kiểm tra netlist với định nghĩa standard-cell.
        yosys -Q -T -l "$checklog" -p "
            read_liberty -lib $LIB
            read_verilog $netlist
            hierarchy -check -top $TOP
            check -assert
            stat -liberty $LIB
        " > /dev/null

        grep -E \
            "Found and reported|Number of cells:|Chip area" \
            "$checklog" | tail -n 3

        echo "PASS: $name"
        echo
    done
done

echo "========== ASIC SWEEP COMPLETED =========="
