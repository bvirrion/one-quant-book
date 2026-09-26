// Parity of the C++20 serving path (flat forest loop and generated branches) with firm_lobmodel.py on data/vectors.csv.
#include <cstdio>
#include <fstream>
#include <sstream>
#include <string>

#include "lobmodel.hpp"

int main() {
  const std::string dir = "code/firm/lobmodel/data/";
  const lobmodel::Model model(dir + "forest.txt");
  std::ifstream in(dir + "vectors.csv");
  std::string line;
  int rows = 0, bad = 0;
  while (std::getline(in, line)) {
    lobmodel::Features x{};
    std::istringstream s(line);
    std::string cell;
    for (int j = 0; j < lobmodel::kFeatures; ++j) {
      std::getline(s, cell, ',');
      x[static_cast<size_t>(j)] = std::stod(cell);
    }
    std::getline(s, cell, ',');
    const double want = std::stod(cell);
    if (model.loop(x) != want || lobmodel::Model::branches(x) != want) ++bad;
    ++rows;
  }
  std::printf("lobmodel: %d rows, %d mismatches\n", rows, bad);
  return (rows == 200 && bad == 0) ? 0 : 1;
}
