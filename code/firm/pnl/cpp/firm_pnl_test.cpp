#include "firm_pnl.hpp"
#include <cassert>
#include <cmath>
#include <random>

using firm::Position;
using firm::Side;

static bool close_to(double a, double b) { return std::fabs(a - b) < 1e-3; }

int main() {
    {   // round trip
        Position p;
        p.on_fill(Side::Buy, 100, 500000);
        p.on_fill(Side::Sell, 100, 501200);
        assert(p.quantity == 0 && close_to(p.realised, 120000) && p.total(1) == 120000);
    }
    {   // average cost, partial close
        Position p;
        p.on_fill(Side::Buy, 100, 500000);
        p.on_fill(Side::Buy, 300, 504000);
        assert(close_to(p.avg_cost, 503000));
        p.on_fill(Side::Sell, 200, 506000);
        assert(close_to(p.realised, 600000) && p.quantity == 200);
    }
    {   // flip
        Position p;
        p.on_fill(Side::Buy, 100, 500000);
        p.on_fill(Side::Sell, 250, 498000);
        assert(p.quantity == -150 && close_to(p.avg_cost, 498000) && close_to(p.realised, -200000));
        assert(close_to(p.unrealised(497000), 150000));
    }
    {   // the split adds up to the exact total
        std::mt19937_64 rng(7);
        Position p;
        for (int i = 0; i < 5000; ++i) {
            const Side s = (rng() & 1) ? Side::Buy : Side::Sell;
            p.on_fill(s, static_cast<std::int64_t>(1 + rng() % 8) * 100,
                      499000 + static_cast<std::int64_t>(rng() % 2000), static_cast<std::int64_t>(rng() % 50));
        }
        const std::int64_t mark = 500250;
        const double split = p.realised + p.unrealised(mark) - static_cast<double>(p.fees);
        assert(std::fabs(split - static_cast<double>(p.total(mark))) < 1.0);
    }
    bool threw = false;
    try { Position{}.on_fill(Side::Buy, 0, 1); } catch (const std::invalid_argument&) { threw = true; }
    assert(threw);
    return threw ? 0 : 1;
}
