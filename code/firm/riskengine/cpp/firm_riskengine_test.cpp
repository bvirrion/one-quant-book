// Acceptance tests of firm.riskengine's C++20 kernel: the fixture shared with the Python and Rust tests.
#include "firm_riskengine.hpp"
#include <cassert>
#include <cmath>

using namespace firm::riskengine;

int main() {
    const int scen = 40, trades = 5;
    Matrix pnl(scen, std::vector<double>(trades));
    for (int i = 0; i < scen; ++i)
        for (int j = 0; j < trades; ++j)
            pnl[i][j] = 10.0 * std::sin(0.7 * i + j) + 3.0 * std::cos(1.3 * i * (j + 1));
    const std::vector<Path> paths = {{"F", "A", "x"}, {"F", "A", "y"}, {"F", "B", "x"}, {"F", "B", "x"}, {"F", "B", "z"}};
    const auto agg = aggregate(pnl, paths);
    assert(agg.size() == 7);
    const std::map<Path, std::pair<double, double>> want = {
        {{"F"}, {14.86618942343704, 14.291194493251536}},
        {{"F", "A"}, {17.809578986609523, 17.830288721860203}},
        {{"F", "B"}, {26.518767856515673, 23.789625576197057}},
        {{"F", "A", "x"}, {10.903557269026098, 10.322188844817205}},
        {{"F", "B", "z"}, {11.674073958581577, 10.951052984889861}}};
    for (const auto& [n, w] : want) {
        assert(std::fabs(var_es(agg.at(n), 0.95).first - w.first) < 1e-9);
        assert(std::fabs(var_es(agg.at(n), 0.90).second - w.second) < 1e-9);
    }
    const auto e = euler_es(agg.at({"F"}), {{{"F", "A"}, agg.at({"F", "A"})}, {{"F", "B"}, agg.at({"F", "B"})}}, 0.90);
    assert(std::fabs(e.at({"F", "A"}) - 1.114894308826234) < 1e-9);
    assert(std::fabs(e.at({"F", "B"}) - 13.176300184425303) < 1e-9);
    assert(std::fabs(e.at({"F", "A"}) + e.at({"F", "B"}) - var_es(agg.at({"F"}), 0.90).second) < 1e-9);
    return 0;
}
