
#!/usr/bin/env bash
set -uo pipefail

cd "$(dirname "$0")/.."
OUT="results/fpga_ice40"
mkdir -p "$OUT"

for arch in P0 P1 P2; do
    case "$arch" in
        P0) rtl="rtl/mac_parameterized.sv"; top="mac_parameterized" ;;
        P1) rtl="rtl/mac_pipeline.sv"; top="mac_pipeline" ;;
        P2) rtl="rtl/mac_pipeline2.sv"; top="mac_pipeline2" ;;
    esac

    for config in C1 C2 C3 C4 C5; do
        case "$config" in
            C1) iw=6;  frac=2;  aw=15 ;;
            C2) iw=8;  frac=4;  aw=19 ;;
            C3) iw=10; frac=6;  aw=23 ;;
            C4) iw=12; frac=8;  aw=27 ;;
            C5) iw=16; frac=12; aw=35 ;;
        esac

        af=$((2 * frac))
        name="${arch}_${config}"

        echo "========== $name =========="

        if ! yosys -Q -T \
            -l "$OUT/${name}_yosys.log" \
            -p "
read_verilog -sv $rtl
hierarchy -top $top -chparam INPUT_WIDTH $iw -chparam INPUT_FRAC $frac -chparam ACC_WIDTH $aw -chparam ACC_FRAC $af -chparam OUTPUT_WIDTH 8 -chparam OUTPUT_FRAC 4
synth_ice40 -top $top -json $OUT/${name}.json
stat
" > /dev/null 2>&1; then
            echo "SYNTHESIS FAILED: $name"
            continue
        fi

        if ! nextpnr-ice40 \
            --hx8k \
            --package ct256 \
            --json "$OUT/${name}.json" \
            --asc "$OUT/${name}.asc" \
            --freq 50 \
            --seed 42 \
            --timing-allow-fail \
            --log "$OUT/${name}_nextpnr.log" \
            > /dev/null 2>&1; then
            echo "PLACE AND ROUTE FAILED: $name"
            continue
        fi

        echo "COMPLETED: $name"
        grep "Max frequency for clock" \
            "$OUT/${name}_nextpnr.log" | tail -n 1
    done
done

echo "========== FPGA SWEEP FINISHED =========="
