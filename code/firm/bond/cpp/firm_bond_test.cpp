// Acceptance tests of firm.bond (C++20): the Treasury's worked examples and the risk identities.
#include "firm_bond.hpp"
#include <cassert>
#include <cmath>

using namespace std::chrono;
using firm::bond::Bond;

static bool near(double a, double b, double tol) { return std::fabs(a - b) < tol; }

int main() {
    {   // 31 CFR 356 App. B, II.A: on a coupon date both conventions give 99.057893
        const Bond b{8.75, year{2020} / May / 15};
        const year_month_day s = year{1990} / May / 15;
        assert(b.accrued(s) == 0.0);
        assert(near(b.clean_price(0.0884, s, true), 99.057893, 5e-7));
        assert(near(b.clean_price(0.0884, s), 99.057893, 5e-7));
    }
    {   // II.D: between coupons, Treasury convention, accrued 0.367403
        const Bond b{9.50, year{1995} / November / 15};
        const year_month_day s = year{1985} / November / 29;
        assert(near(b.accrued(s), 0.367403, 5e-7));
        assert(near(b.clean_price(0.0954, s, true), 99.730918, 5e-7));
    }
    {   // end-of-month schedule through a leap year
        const Bond b{4.0, year{2028} / August / 31};
        year_month_day prev, next;
        int n = 0;
        b.locate(year{2028} / March / 10, prev, next, n);
        assert(prev == year{2028} / February / 29 && next == year{2028} / August / 31 && n == 1);
    }
    {   // yield round trip, DV01 against a bump
        const Bond b{4.25, year{2036} / August / 15};
        const year_month_day s = year{2026} / September / 25;
        assert(near(b.yield_from_clean(b.clean_price(0.042, s), s), 0.042, 1e-12));
        const auto r = b.risk(0.042, s);
        const double bump = (b.dirty_price(0.0419, s) - b.dirty_price(0.0421, s)) / 2.0;
        assert(near(r.dv01, bump, 1e-6 * r.dv01));
        assert(r.modified < r.macaulay && r.convexity > 0.0);
    }
    return 0;
}
