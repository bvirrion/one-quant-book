// Acceptance tests of firm.pblimits (C++20): the same cases as the Python reference.
#include "firm_pblimits.hpp"
#include <cassert>
#include <cmath>

using namespace firm::pblimits;

static std::vector<Book> books() {
    return {Book({"A", 3, 100e6, 500e6, 7, {"EURUSD", "USDJPY"}}),
            Book({"B", 5, 150e6, 600e6, 30, {"EURUSD", "USDJPY", "GBPUSD"}}),
            Book({"C", 8, 300e6, 1000e6, 370, {"EURUSD", "USDJPY", "GBPUSD", "USDMXN"}})};
}

int main() {
    const Usd usd{{"USD", 1.0}, {"EUR", 1.10}, {"JPY", 1.0 / 150}, {"GBP", 1.30}, {"MXN", 1.0 / 18}};
    {
        Book a = books()[0];
        a.apply({"EURUSD", true, 50e6, 1.10, 2}, usd);
        assert(std::fabs(a.nop() - 55e6) < 1e-6 && std::fabs(a.settlement(2) - 55e6) < 1e-6);
        a.apply({"USDJPY", true, 20e6, 150.0, 2}, usd);
        assert(std::fabs(a.nop() - 55e6) < 1e-6 && std::fabs(a.settlement(2) - 55e6) < 1e-6);
    }
    {
        Book a = books()[0];
        assert(a.check({"EURUSD", true, 95e6, 1.10, 2}, usd) == Decision::nop);
        a.apply({"EURUSD", true, 90e6, 1.10, 2}, usd);
        a.limits.nop_limit = 50e6;
        assert(a.check({"EURUSD", true, 1e6, 1.10, 2}, usd) == Decision::nop);
        assert(a.check({"EURUSD", false, 10e6, 1.10, 2}, usd) == Decision::ok);
        assert(a.check({"GBPUSD", true, 1e6, 1.30, 2}, usd) == Decision::pair);
        assert(a.check({"EURUSD", true, 1e6, 1.10, 30}, usd) == Decision::tenor);
    }
    {
        Book b = books()[1];
        b.limits.nop_limit = 1e12;
        b.apply({"EURUSD", true, 500e6, 1.10, 2}, usd);
        assert(b.check({"EURUSD", true, 50e6, 1.10, 2}, usd) == Decision::settlement);
        assert(b.check({"EURUSD", true, 50e6, 1.10, 3}, usd) == Decision::ok);
    }
    {
        auto bs = books();
        assert(route(bs, {"EURUSD", true, 80e6, 1.10, 2}, usd) == "A");
        assert(route(bs, {"EURUSD", true, 80e6, 1.10, 2}, usd) == "B");
        assert(route(bs, {"USDMXN", true, 10e6, 18.0, 2}, usd) == "C");
    }
    return 0;
}
