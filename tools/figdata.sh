#!/usr/bin/env bash
# Regenerate chart CSVs: runs every code/<slug>/<chapter>/python/fig_*.py
# (each writes into figdata/<slug>/<chapter>/). Deterministic: no diff expected.
# Measured data (Book 13's timings) comes from bench_*.py drivers writing
# figdata/<slug>/<chapter>/measured_*.csv + a .meta sidecar; they are never run here.
set -euo pipefail
cd "$(dirname "$0")/.."
# Many small matrix products: BLAS threads only add overhead (a 12-second model took 6.5 minutes with them).
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}" OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
sel="${1:-}"
find "code/${sel}" -name 'fig_*.py' | sort | while read -r f; do
  echo "figdata: $f"; .venv/bin/python "$f"
done
