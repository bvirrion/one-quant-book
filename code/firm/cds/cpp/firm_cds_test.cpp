// Acceptance tests of firm.cds (C++20): the same numbers as the Python build.
#include "firm_cds.hpp"
#include <cassert>
#include <cmath>

using namespace firm::cds;

static bool near(double a, double b, double tol) { return std::fabs(a - b) < tol; }

int main() {
    const Cds ig{5.0, 0.01};
    const double lam = hazard_from_spread(ig, 0.01, 0.04);
    assert(near(lam, 0.0166666908, 1e-9));
    assert(near(par_spread(ig, lam, 0.04), 0.01, 1e-12));
    assert(near(upfront(ig, hazard_from_spread(ig, 0.02, 0.04), 0.04), 0.0416490885, 1e-9));
    // Lehman Brothers, 10 October 2008: first stage (FRBNY Staff Report 372, Box 1)
    const std::vector<double> bids{8, 8, 8, 8, 8.25, 8.75, 8.875, 9, 9, 9.25, 9.25, 9.5, 9.5, 10};
    const std::vector<double> offers{10, 10, 10, 10, 10.25, 10.75, 10.875, 11, 11, 11, 11.25, 11.5, 11.5, 12};
    assert(inside_market_midpoint(bids, offers) == 9.75);
    const std::vector<std::pair<double, double>> orders{{11.0, 100}, {10.0, 400}, {9.0, 1500}, {8.625, 3000}, {7.0, 5000}};
    assert(final_price(9.75, 4920, orders) == 8.625);
    assert(final_price(9.75, 4920, {{12.0, 6000}}) == 10.75);
    assert(cash_settlement(10e6, 8.625) == 9137500.0);
    return 0;
}
