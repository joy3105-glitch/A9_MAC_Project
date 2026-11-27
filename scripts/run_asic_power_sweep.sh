#!/usr/bin/env bash
set -euo pipefail

cd ~/A9_MAC_Project

IMAGE="ghcr.io/the-openroad-project/openlane:ff5509f65b17bfa4068d5336495ab1718987ff69"

OUT="results/asic_sky130_filtered/power"

mkdir -p "$OUT"

for arch in P0 P1 P2
do
    for cfg in C1 C2 C3 C4 C5
    do
        echo "========== POWER $arch $cfg =========="

        LOG="$OUT/${arch}_${cfg}_power.log"

        docker run --rm \
            -v "$PWD:/work:ro" \
            -e MAC_ARCH="$arch" \
            -e MAC_CFG="$cfg" \
            --entrypoint /bin/bash \
            "$IMAGE" \
            -lc 'sta -exit /work/scripts/sta/run_mac_power.tcl' \
            > "$LOG" 2>&1

        if ! grep -q "POWER COMPLETE" "$LOG"; then
            echo "ERROR: Power estimation incomplete"
            cat "$LOG"
            exit 1
        fi

        if grep -Eq '(^|[[:space:]])(Error:|Warning:)' "$LOG"; then
            echo "ERROR/WARNING: Check $LOG"
            cat "$LOG"
            exit 1
        fi

        if ! grep -Eq '^Total[[:space:]]+[0-9]' "$LOG"; then
            echo "ERROR: Missing total power result"
            exit 1
        fi

        grep -E '^Total[[:space:]]' "$LOG"

        echo "POWER RESULT: PASS"
        echo
    done
done

echo "========== ALL POWER RUNS COMPLETE =========="
