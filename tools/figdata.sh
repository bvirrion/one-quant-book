#!/usr/bin/env bash
# Regenerate chart CSVs: runs every code/<slug>/<chapter>/python/fig_*.py
# (each writes into figdata/<slug>/<chapter>/). Deterministic: no diff expected.
set -euo pipefail
cd "$(dirname "$0")/.."
sel="${1:-}"
find "code/${sel}" -name 'fig_*.py' | sort | while read -r f; do
  echo "figdata: $f"; .venv/bin/python "$f"
done
