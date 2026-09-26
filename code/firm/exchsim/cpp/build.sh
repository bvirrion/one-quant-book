#!/usr/bin/env bash
# Builds the live server: code/firm/exchsim/cpp/bin/exchsim_server
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p bin
g++ -std=c++20 -O2 -Wall -Wextra -Werror -I. exchsim_server.cpp -o bin/exchsim_server
echo "built $(pwd)/bin/exchsim_server"
