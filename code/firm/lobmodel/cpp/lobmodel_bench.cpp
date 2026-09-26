// Latency of the C++20 serving path, one call at a time (built and run by bench_lobmodel.py; not a test).
#include <algorithm>
#include <chrono>
#include <cstdio>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

#include "lobmodel.hpp"

template <typename F>
void measure(const char* name, F&& f, const std::vector<lobmodel::Features>& rows) {
  std::vector<double> t;
  t.reserve(200000);
  volatile double sink = 0.0;
  for (int k = 0; k < 200000; ++k) {
    const auto& x = rows[static_cast<size_t>(k) % rows.size()];
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
  const std::string dir = "code/firm/lobmodel/data/";
  const lobmodel::Model model(dir + "forest.txt");
  std::vector<lobmodel::Features> rows;
  std::ifstream in(dir + "vectors.csv");
  std::string line;
  while (std::getline(in, line)) {
    lobmodel::Features x{};
    std::istringstream s(line);
    std::string cell;
    for (auto& v : x) {
      std::getline(s, cell, ',');
      v = std::stod(cell);
    }
    rows.push_back(x);
  }
  measure("cpp forest loop", [&](const lobmodel::Features& x) { return model.loop(x); }, rows);
  measure("cpp forest branches", [&](const lobmodel::Features& x) { return lobmodel::Model::branches(x); }, rows);
  measure("clock overhead", [&](const lobmodel::Features& x) { return x[0]; }, rows);
  return 0;
}
