#!/usr/bin/env bash
set -euo pipefail

cd ~/A9_MAC_Project

IMAGE="ghcr.io/the-openroad-project/openlane:ff5509f65b17bfa4068d5336495ab1718987ff69"

OUT="results/asic_sky130_filtered/timing"
mkdir -p "$OUT"

for arch in P0 P1 P2
do
    for cfg in C1 C2 C3 C4 C5
    do
        echo "========== $arch $cfg =========="

        docker run --rm \
            -v "$PWD:/work:ro" \
            -e MAC_ARCH="$arch" \
            -e MAC_CFG="$cfg" \
            --entrypoint /bin/bash \
            "$IMAGE" \
            -lc 'sta -exit /work/scripts/sta/run_mac_sta.tcl' \
            > "$OUT/${arch}_${cfg}_timing.log" 2>&1

        if ! grep -q "STA COMPLETE" "$OUT/${arch}_${cfg}_timing.log"; then
            echo "ERROR: STA did not complete for $arch $cfg"
            exit 1
        fi

        if grep -Eq '(^|[[:space:]])(Error:|Warning:)' "$OUT/${arch}_${cfg}_timing.log"; then
            echo "WARNING/ERROR: Check $OUT/${arch}_${cfg}_timing.log"
            exit 1
        fi

        grep -E 'worst slack|tns' \
            "$OUT/${arch}_${cfg}_timing.log"
    done
done

echo "========== ALL STA RUNS COMPLETE =========="
