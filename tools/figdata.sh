#!/usr/bin/env bash
# Regenerate chart CSVs: runs every code/<slug>/<chapter>/python/fig_*.py
# (each writes into figdata/<slug>/<chapter>/). Deterministic: no diff expected.
# Measured data (Book 13's timings) comes from bench_*.py drivers writing
# figdata/<slug>/<chapter>/measured_*.csv + a .meta sidecar; they are never run here.
set -euo pipefail
cd "$(dirname "$0")/.."
# Many small matrix products: BLAS threads only add overhead (a 12-second model took 6.5 minutes with them).
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}" OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
# Same floating-point kernels on every x86-64 machine as on the one that wrote the numbers (Haswell-class
# AVX2, no AVX-512; each pin is what this machine picks anyway): other kernels sum in another order.
export OPENBLAS_CORETYPE="${OPENBLAS_CORETYPE:-Haswell}" ATEN_CPU_CAPABILITY="${ATEN_CPU_CAPABILITY:-avx2}" \
  ONEDNN_MAX_CPU_ISA="${ONEDNN_MAX_CPU_ISA:-AVX2}" \
  NPY_DISABLE_CPU_FEATURES="${NPY_DISABLE_CPU_FEATURES-AVX512F AVX512CD AVX512_KNL AVX512_KNM AVX512_SKX AVX512_CLX AVX512_CNL AVX512_ICL}"
sel="${1:-}"
find "code/${sel}" -name 'fig_*.py' | sort | while read -r f; do
  echo "figdata: $f"; .venv/bin/python "$f"
done
