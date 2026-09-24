// Acceptance tests of firm.fdpricer (C++20): the uniform-grid American put agrees with the Python engine to
// rounding, is above the European price and below the strike, and converges as the grid is refined.
#include "firm_fdpricer.hpp"
#include <cassert>
#include <cmath>

using namespace firm::fdpricer;

static bool near(double a, double b, double tol) { return std::fabs(a - b) < tol; }

int main() {
    // reference values from firm_fdpricer.py (grid="uniform", smoothing=False)
    assert(near(american_put(100, 100, 1.0, 0.05, 0.0, 0.2, 200, 200), 6.08735366060978, 1e-9));
    assert(near(american_put(90, 100, 0.5, 0.03, 0.01, 0.3, 160, 100), 13.389843531304049, 1e-9));
    assert(near(american_put(100, 100, 1.0, 0.05, 0.0, 0.2, 200, 200, 0), 6.087606072487043, 1e-9));
    const double coarse = american_put(100, 100, 1.0, 0.05, 0.0, 0.2, 100, 100);
    const double fine = american_put(100, 100, 1.0, 0.05, 0.0, 0.2, 400, 400);
    assert(std::fabs(fine - 6.0903534672) < std::fabs(coarse - 6.0903534672));
    assert(fine > 5.5735 && fine < 100.0);
    return 0;
}
