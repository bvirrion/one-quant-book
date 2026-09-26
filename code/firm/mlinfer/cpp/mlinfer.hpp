// firm.mlinfer -- C++20 inference kernels for a flat forest and an int8 multilayer perceptron (Book 12, chapter 26).
// Loading allocates; predict() does not: fixed-size buffers on the stack, no exceptions, no virtual calls.
// Bit-for-bit parity with firm_mlinfer.py (forest_predict, int8_forward) on data/vectors.csv.
#pragma once
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

namespace mlinfer {

struct Forest {
  std::vector<int32_t> roots, feature, left, right;
  std::vector<double> threshold, value;

  double predict(const double* x) const {
    double s = 0.0;
    for (int32_t n : roots) {
      while (n >= 0) n = x[feature[n]] <= threshold[n] ? left[n] : right[n];
      s += value[static_cast<size_t>(-n - 1)];
    }
    return s;
  }
};

template <typename T>
inline std::vector<T> numbers(std::istringstream& in) {
  std::vector<T> v;
  T x;
  while (in >> x) v.push_back(x);
  return v;
}

inline Forest read_forest(const std::string& path) {
  Forest f;
  std::ifstream in(path);
  std::string line;
  while (std::getline(in, line)) {
    std::istringstream s(line);
    std::string key;
    s >> key;
    if (key == "roots") f.roots = numbers<int32_t>(s);
    else if (key == "feature") f.feature = numbers<int32_t>(s);
    else if (key == "left") f.left = numbers<int32_t>(s);
    else if (key == "right") f.right = numbers<int32_t>(s);
    else if (key == "threshold") f.threshold = numbers<double>(s);
    else if (key == "value") f.value = numbers<double>(s);
  }
  return f;
}

struct Layer {
  int out = 0, in = 0;
  int64_t mult = 0;
  int shift = 0;
  double prod = 0.0;
  std::vector<int32_t> w, b;
};

constexpr int kMaxWidth = 64;

// round(acc * mult / 2^shift), halves away from zero, clamped to int8.
inline int64_t requant(int64_t acc, int64_t mult, int shift) {
  const int64_t p = acc * mult;
  const int64_t r = ((p < 0 ? -p : p) + (int64_t{1} << (shift - 1))) >> shift;
  return std::clamp<int64_t>(p < 0 ? -r : r, -127, 127);
}

struct Mlp {
  double s_in = 1.0;
  std::vector<Layer> layers;

  double predict(const double* x) const {
    std::array<int64_t, kMaxWidth> a{}, b{};
    const Layer& first = layers.front();
    for (int i = 0; i < first.in; ++i)
      a[static_cast<size_t>(i)] = std::clamp<int64_t>(static_cast<int64_t>(std::nearbyint(x[i] / s_in)), -127, 127);
    for (size_t l = 0; l < layers.size(); ++l) {
      const Layer& L = layers[l];
      for (int o = 0; o < L.out; ++o) {
        int64_t acc = L.b[static_cast<size_t>(o)];
        const int32_t* row = &L.w[static_cast<size_t>(o * L.in)];
        for (int i = 0; i < L.in; ++i) acc += static_cast<int64_t>(row[i]) * a[static_cast<size_t>(i)];
        if (l + 1 == layers.size()) return static_cast<double>(acc) * L.prod;
        b[static_cast<size_t>(o)] = std::max<int64_t>(requant(acc, L.mult, L.shift), 0);
      }
      a = b;
    }
    return 0.0;
  }
};

inline Mlp read_mlp(const std::string& path) {
  Mlp m;
  std::ifstream in(path);
  std::string line;
  while (std::getline(in, line)) {
    std::istringstream s(line);
    std::string key;
    s >> key;
    if (key == "s_in") s >> m.s_in;
    else if (key == "layer") {
      Layer L;
      s >> L.out >> L.in >> L.mult >> L.shift >> L.prod;
      m.layers.push_back(L);
    } else if (key == "W") m.layers.back().w = numbers<int32_t>(s);
    else if (key == "B") m.layers.back().b = numbers<int32_t>(s);
  }
  return m;
}

}  // namespace mlinfer
