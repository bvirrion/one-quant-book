// Acceptance tests of firm.bs (C++20): the textbook value, parity, Greeks against finite
// differences, and implied-volatility round trips across moneyness and maturity.
#include "firm_bs.hpp"
#include <cassert>
#include <cmath>

using namespace firm::bs;

static bool near(double a, double b, double tol) { return std::fabs(a - b) < tol; }

int main() {
    assert(near(bs(100, 100, 1, 0.05, 0, 0.2, Right::Call), 10.450583572185579, 1e-12));
    {   // put-call parity with a dividend yield
        const double c = bs(100, 110, 0.5, 0.03, 0.01, 0.25, Right::Call);
        const double p = bs(100, 110, 0.5, 0.03, 0.01, 0.25, Right::Put);
        assert(near(c - p, 100 * std::exp(-0.01 * 0.5) - 110 * std::exp(-0.03 * 0.5), 1e-12));
    }
    {   // Greeks against central differences
        const double h = 1e-4;
        const Greeks g = greeks(100, 110, 0.5, 0.03, 0.01, 0.25, Right::Put);
        auto P = [](double s, double t, double r, double v) { return bs(s, 110, t, r, 0.01, v, Right::Put); };
        assert(near(g.delta, (P(100 + h, .5, .03, .25) - P(100 - h, .5, .03, .25)) / (2 * h), 1e-7));
        assert(near(g.gamma, (P(100 + h, .5, .03, .25) - 2 * P(100, .5, .03, .25) + P(100 - h, .5, .03, .25)) / (h * h), 1e-4));
        assert(near(g.vega, (P(100, .5, .03, .25 + h) - P(100, .5, .03, .25 - h)) / (2 * h), 1e-6));
        assert(near(g.rho, (P(100, .5, .03 + h, .25) - P(100, .5, .03 - h, .25)) / (2 * h), 1e-6));
        assert(near(g.theta, -(P(100, .5 + h, .03, .25) - P(100, .5 - h, .03, .25)) / (2 * h), 1e-5));
    }
    for (double k : {40.0, 80.0, 100.0, 125.0, 300.0})
        for (double t : {0.01, 0.25, 1.0, 10.0})
            for (double v : {0.05, 0.2, 0.8}) {
                for (Right r : {Right::Call, Right::Put}) {
                    const double p = black(100, k, t, 0.97, v, r);
                    if (p < 1e-8) continue;
                    const double iv = implied_vol(p, 100, k, t, 0.97, r);
                    assert(near(black(100, k, t, 0.97, iv, r), p, 1e-10 * std::max(p, 1.0)));
                }
            }
    bool threw = false;
    try { implied_vol(0.5, 100, 80, 1, 1, Right::Call); } catch (const std::domain_error&) { threw = true; }
    assert(threw);
    return 0;
}
