// Parity of the C++20 kernels (flat forest, generated branches, int8 MLP) with the Python reference on data/vectors.csv.
#include <cstdio>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

#include "forest_branches.hpp"
#include "mlinfer.hpp"

int main() {
  const std::string dir = "code/firm/mlinfer/data/";
  const auto forest = mlinfer::read_forest(dir + "forest.txt");
  const auto mlp = mlinfer::read_mlp(dir + "mlp.txt");
  std::ifstream in(dir + "vectors.csv");
  std::string line;
  int rows = 0, bad = 0;
  while (std::getline(in, line)) {
    std::vector<double> v;
    std::istringstream s(line);
    std::string cell;
    while (std::getline(s, cell, ',')) v.push_back(std::stod(cell));
    const double* x = v.data();
    const double want_forest = v[16], want_mlp = v[17];
    if (forest.predict(x) != want_forest || forest_branches(x) != want_forest || mlp.predict(x) != want_mlp) ++bad;
    ++rows;
  }
  std::printf("mlinfer: %d rows, %d mismatches\n", rows, bad);
  return (rows == 200 && bad == 0) ? 0 : 1;
}
