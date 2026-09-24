// Acceptance tests of firm.pricing's C++20 core: dates, forwards, bumps, and the analytic and finite-difference
// engines and their Greeks agree with firm_pricing.py to 1e-9 on the same snapshot.
#include "pricing.hpp"
#include <cassert>
#include <cmath>

using namespace firm::pricing;

static bool near(double a, double b, double tol) { return std::fabs(a - b) < tol; }

int main() {
    const Date t0{2026, 9, 24}, e{2027, 9, 24};
    assert(days_from_civil({1970, 1, 1}) == 0 && days_from_civil(e) - days_from_civil(t0) == 365);
    assert(civil_from_days(days_from_civil({2028, 2, 29})).d == 29);
    MarketData md{t0, {{"ABC", 100.0}}, {{"USD", FlatCurve{0.05, t0}}}, {{"ABC", Dividends{0.02, 0.005}}},
                  {{"ABC", 0.2}}, {}};
    assert(near(md.forward("ABC", e), 102.53151205244288, 1e-12));
    EuropeanOption call{"o", "ABC", "USD", 1.0, "", 100.0, e, true, false};
    EuropeanOption put = call;
    put.call = false;
    put.strike = 95.0;
    EuropeanOption amput = call, amcall = call;
    amput.call = false;
    amput.american = true;
    amput.strike = 110.0;
    amcall.american = true;
    amcall.strike = 90.0;
    const AnalyticEngine an;
    const PDEEngine pde;
    // reference values from firm_pricing.py
    assert(near(an.price(call, md), 8.93667801992408, 1e-9));
    assert(near(an.price(put, md), 4.437332869541783, 1e-9));
    assert(near(pde.price(call, md), 8.934340456890846, 1e-9));
    assert(near(pde.price(put, md), 4.436150972443718, 1e-9));
    assert(near(pde.price(amput, md), 12.78912756690443, 1e-9));
    assert(near(pde.price(amcall, md), 14.743700892073113, 1e-9));
    assert(near(fd_vanilla(100, 100, 1.0, 0.05, 0.0, 0.2, false, true), 6.0873536606097804, 1e-9));
    const Greeks ga = greeks(amput, md, pde);
    assert(near(ga.delta, -0.6386648197036005, 1e-9) && near(ga.gamma, 2.2805489998388495, 1e-8));
    assert(near(ga.vega, 0.353233112561127, 1e-9) && near(ga.theta, -0.006380588425209055, 1e-9));
    assert(near(ga.rho, -0.004244035535873714, 1e-9));
    const Greeks gc = greeks(call, md, an);
    assert(near(gc.delta, 0.5744004983176145, 1e-9) && near(gc.gamma, 1.8965451250293697, 1e-8));
    assert(near(gc.vega, 0.3793580615602945, 1e-9) && near(gc.theta, -0.013112603398962364, 1e-9));
    assert(near(gc.rho, 0.004851008590838646, 1e-9));
    // snapshots are immutable; bumps return new ones
    const MarketData up = md.apply({"SPOT:ABC", 0.01, true});
    assert(md.spots.at("ABC") == 100.0 && near(up.spots.at("ABC"), 101.0, 1e-12));
    assert(pde.price(amput, md) > an.price(EuropeanOption{"x", "ABC", "USD", 1.0, "", 110.0, e, false, false}, md));
    return 0;
}
