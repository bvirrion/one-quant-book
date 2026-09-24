// Acceptance tests of firm.pde (C++20): the Crank-Nicolson call of chapter 27 against the Python twin and
// Black-Scholes, the sawtooth and its removal by Rannacher start-up.
#include "firm_pde.hpp"
#include <algorithm>
#include <cassert>
#include <cmath>

using namespace firm::pde;

int main() {
    const double K = 100.0, r = 0.03, sigma = 0.2, T = 0.25;
    const double lo = 4.105170185988092, hi = 5.105170185988092;       // ln K -/+ 5 sigma sqrt(T), as in Python
    const int n = 400;
    std::vector<double> x(n + 1), pay(n + 1);
    const double step = (hi - lo) / n;
    for (int i = 0; i <= n; ++i) x[i] = i * step + lo;
    x[n] = hi;
    for (int i = 0; i <= n; ++i) pay[i] = std::max(std::exp(x[i]) - K, 0.0);
    const double a = 0.5 * sigma * sigma, b = r - 0.5 * sigma * sigma;
    const auto cn = solve_1d(x, pay, a, b, r, T, 25, 0.5, 0);
    const auto cn4 = solve_1d(x, pay, a, b, r, T, 25, 0.5, 4);
    // the Python twin's values at the strike node and at node 180
    assert(std::fabs(cn[200] - 4.375764376609226) < 1e-11 && std::fabs(cn[180] - 2.155015812022793) < 1e-11);
    assert(std::fabs(cn4[200] - 4.3567077082780585) < 1e-11 && std::fabs(cn4[180] - 2.154527540626845) < 1e-11);
    // Black-Scholes 4.3576193; the second difference at the strike: a sawtooth without start-up, smooth with it
    assert(std::fabs(cn4[200] - 4.3576193334575635) < 1e-3);
    assert(cn[201] - 2 * cn[200] + cn[199] < 0 && cn4[201] - 2 * cn4[200] + cn4[199] > 0);
    return 0;
}
