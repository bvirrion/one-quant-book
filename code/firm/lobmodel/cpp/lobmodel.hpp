// firm.lobmodel -- the C++20 serving path of the chapter 29 order-book model (Book 12): the flat forest of
// firm.mlinfer and the generated branches, behind one call that takes the ten features in FEATURES order.
#pragma once

#include <array>
#include <string>

#include "../../mlinfer/cpp/mlinfer.hpp"
#include "lobmodel_branches.hpp"

namespace lobmodel {

inline constexpr int kFeatures = 10;
using Features = std::array<double, kFeatures>;

struct Model {
  mlinfer::Forest forest;
  explicit Model(const std::string& path) : forest(mlinfer::read_forest(path)) {}
  double loop(const Features& x) const { return forest.predict(x.data()); }
  static double branches(const Features& x) { return lobmodel_branches(x.data()); }
};

}  // namespace lobmodel
