#!/usr/bin/env bash
# After tools/figdata.sh: fail if any regenerated chart CSV differs from the
# committed one, except the files listed in figdata/MACHINE_DEPENDENT.txt
# (noise-level values whose digits move with the processor; one path per line,
# '#' starts a comment, each entry needs its reason).
set -euo pipefail
cd "$(dirname "$0")/.."
excl=()
if [ -f figdata/MACHINE_DEPENDENT.txt ]; then
  while IFS= read -r line; do
    p="${line%%#*}"; p="${p//[[:space:]]/}"
    [ -n "$p" ] && excl+=(":(exclude)$p")
  done < figdata/MACHINE_DEPENDENT.txt
fi
git diff --exit-code -- figdata/ "${excl[@]}"
echo "figdata: no diff"
