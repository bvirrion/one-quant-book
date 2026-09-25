#!/usr/bin/env bash
# Regenerate chart CSVs: runs every code/<slug>/<chapter>/python/fig_*.py
# (each writes into figdata/<slug>/<chapter>/). Deterministic: no diff expected.
set -euo pipefail
cd "$(dirname "$0")/.."
# Many small matrix products: BLAS threads only add overhead (a 12-second model took 6.5 minutes with them).
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}" OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
sel="${1:-}"
find "code/${sel}" -name 'fig_*.py' | sort | while read -r f; do
  echo "figdata: $f"; .venv/bin/python "$f"
done
