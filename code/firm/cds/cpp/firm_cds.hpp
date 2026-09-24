#pragma once
// firm.cds -- credit default swaps with a flat hazard rate, and the settlement auction (build of
// Chapter 23, One Quant Book 2), C++20. Twin of firm_cds.py: quarterly premiums, half a period of
// accrued premium on default, default paid at the period's end; auction prices per 100 of par.
#include <algorithm>
#include <cmath>
#include <functional>
#include <utility>
#include <vector>

namespace firm::cds {

struct Cds {
    double maturity;          // years
    double coupon;            // running coupon, decimal
    double recovery = 0.40;
    int freq = 4;
};

struct Legs { double annuity, protection; };

inline Legs legs(const Cds& c, double lam, double r) {
    const double dt = 1.0 / c.freq;
    const int n = static_cast<int>(std::lround(c.maturity * c.freq));
    Legs out{0.0, 0.0};
    for (int k = 1; k <= n; ++k) {
        const double q0 = std::exp(-lam * (k - 1) * dt), q1 = std::exp(-lam * k * dt);
        const double df = std::exp(-r * k * dt);
        out.annuity += dt * df * (q1 + 0.5 * (q0 - q1));
        out.protection += (1.0 - c.recovery) * df * (q0 - q1);
    }
    return out;
}

inline double par_spread(const Cds& c, double lam, double r) {
    const Legs l = legs(c, lam, r);
    return l.protection / l.annuity;
}

inline double upfront(const Cds& c, double lam, double r) {
    const Legs l = legs(c, lam, r);
    return l.protection - c.coupon * l.annuity;
}

inline double hazard_from_spread(const Cds& c, double spread, double r) {
    double lo = 1e-9, hi = 5.0;
    for (int i = 0; i < 200; ++i) {
        const double mid = 0.5 * (lo + hi);
        (par_spread(c, mid, r) < spread ? lo : hi) = mid;
    }
    return 0.5 * (lo + hi);
}

inline double inside_market_midpoint(std::vector<double> bids, std::vector<double> offers) {
    std::sort(bids.begin(), bids.end(), std::greater<>());
    std::sort(offers.begin(), offers.end());
    std::size_t i = 0;
    while (i < bids.size() && i < offers.size() && bids[i] >= offers[i]) ++i;
    const std::size_t nb = bids.size() - i, h = (nb + 1) / 2;
    double sum = 0.0;
    for (std::size_t k = 0; k < h; ++k) sum += bids[i + k] + offers[i + k];
    return std::round(sum / (2.0 * static_cast<double>(h)) * 8.0) / 8.0;
}

// orders: (price, size); oi > 0 means the open interest is to sell bonds.
inline double final_price(double imm, double oi, std::vector<std::pair<double, double>> orders) {
    if (oi == 0.0) return imm;
    double filled = 0.0, price = imm;
    if (oi > 0.0) {
        std::sort(orders.begin(), orders.end(), [](auto a, auto b) { return a.first > b.first; });
        for (auto [p, s] : orders) { filled += s; price = p; if (filled >= oi) break; }
        return std::min(price, imm + 1.0);
    }
    std::sort(orders.begin(), orders.end());
    for (auto [p, s] : orders) { filled += s; price = p; if (filled >= -oi) break; }
    return std::max(price, imm - 1.0);
}

inline double cash_settlement(double notional, double price) { return notional * (100.0 - price) / 100.0; }

}  // namespace firm::cds
