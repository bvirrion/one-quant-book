// Latency of the C++20 kernels, one call at a time (built and run by bench_infer.py; not a test).
#include <algorithm>
#include <chrono>
#include <cstdio>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

#include "forest_branches.hpp"
#include "mlinfer.hpp"

template <typename F>
void measure(const char* name, F&& f, const std::vector<std::vector<double>>& rows) {
  std::vector<double> t;
  t.reserve(200000);
  volatile double sink = 0.0;
  for (int k = 0; k < 200000; ++k) {
    const double* x = rows[static_cast<size_t>(k) % rows.size()].data();
    const auto t0 = std::chrono::steady_clock::now();
    sink = sink + f(x);
    const auto t1 = std::chrono::steady_clock::now();
    t.push_back(std::chrono::duration<double, std::nano>(t1 - t0).count());
  }
  std::sort(t.begin(), t.end());
  auto q = [&](double p) { return t[static_cast<size_t>(p * static_cast<double>(t.size() - 1))]; };
  std::printf("%s,%.1f,%.1f,%.1f\n", name, q(0.5), q(0.99), q(0.999));
}

int main() {
  const std::string dir = "code/firm/mlinfer/data/";
  const auto forest = mlinfer::read_forest(dir + "forest.txt");
  const auto mlp = mlinfer::read_mlp(dir + "mlp.txt");
  std::vector<std::vector<double>> rows;
  std::ifstream in(dir + "vectors.csv");
  std::string line;
  while (std::getline(in, line)) {
    std::vector<double> v;
    std::istringstream s(line);
    std::string cell;
    while (std::getline(s, cell, ',')) v.push_back(std::stod(cell));
    rows.push_back(v);
  }
  measure("cpp forest loop", [&](const double* x) { return forest.predict(x); }, rows);
  measure("cpp forest branches", [&](const double* x) { return forest_branches(x); }, rows);
  measure("cpp int8 mlp", [&](const double* x) { return mlp.predict(x); }, rows);
  measure("clock overhead", [&](const double* x) { return x[0]; }, rows);
  return 0;
}
