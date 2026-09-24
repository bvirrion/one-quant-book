// firm.pricing (C++20 twin of the core): dates, flat curves, market-data snapshots with bumps, European and American
// options, the analytic (Black) and finite-difference engines, and desk-unit Greeks by bump-and-reprice. The same
// arithmetic as firm_pricing.py (AnalyticEngine, PDEEngine, fd_vanilla, greeks) for flat curves and volatilities.
#pragma once
#include <algorithm>
#include <cmath>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>

#include "../../bs/cpp/firm_bs.hpp"

namespace firm::pricing {

struct Date {
    int y, m, d;
};

// Days since 1970-01-01 of a proleptic Gregorian date (H. Hinnant's days_from_civil).
inline long days_from_civil(Date x) {
    const int y = x.y - (x.m <= 2 ? 1 : 0);
    const long era = (y >= 0 ? y : y - 399) / 400;
    const long yoe = y - era * 400;
    const long mp = (x.m + 9) % 12;
    const long doy = (153 * mp + 2) / 5 + x.d - 1;
    const long doe = yoe * 365 + yoe / 4 - yoe / 100 + doy;
    return era * 146097 + doe - 719468;
}

inline Date civil_from_days(long z) {
    z += 719468;
    const long era = (z >= 0 ? z : z - 146096) / 146097;
    const long doe = z - era * 146097;
    const long yoe = (doe - doe / 1460 + doe / 36524 - doe / 146096) / 365;
    const long doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    const long mp = (5 * doy + 2) / 153;
    const int d = static_cast<int>(doy - (153 * mp + 2) / 5 + 1);
    const int m = static_cast<int>(mp < 10 ? mp + 3 : mp - 9);
    return {static_cast<int>(yoe + era * 400 + (m <= 2 ? 1 : 0)), m, d};
}

inline double year_fraction(Date a, Date b) { return static_cast<double>(days_from_civil(b) - days_from_civil(a)) / 365.0; }

struct FlatCurve {
    double rate;
    Date asof;
    double df(Date d) const { return std::exp(-rate * year_fraction(asof, d)); }
};

struct Dividends {
    double div_yield = 0.0, borrow = 0.0;
};

struct Bump {
    std::string factor;  // SPOT:<und>, VOL:<und>, CURVE:<name>, DIV:<und>, BORROW:<und>, TIME
    double size;
    bool relative = false;
};

struct MarketData {
    Date asof;
    std::map<std::string, double> spots;
    std::map<std::string, FlatCurve> curves;
    std::map<std::string, Dividends> dividends;
    std::map<std::string, double> vols;  // flat volatility per underlying
    std::map<std::string, std::string> funding;

    double t(Date d) const { return year_fraction(asof, d); }
    double df(const std::string& curve, Date d) const {
        const FlatCurve& c = curves.at(curve);
        return c.df(d) / c.df(asof);
    }
    std::string funding_curve(const std::string& und) const {
        if (auto it = funding.find(und); it != funding.end()) return it->second;
        if (curves.size() == 1) return curves.begin()->first;
        throw std::invalid_argument("no funding curve for " + und);
    }
    double forward(const std::string& und, Date d) const {
        const std::string c = funding_curve(und);
        Dividends div;
        if (auto it = dividends.find(und); it != dividends.end()) div = it->second;
        return spots.at(und) * std::exp(-(div.borrow + div.div_yield) * t(d)) / df(c, d);
    }
    MarketData rolled(Date new_asof) const {
        MarketData out = *this;
        out.asof = new_asof;
        return out;
    }
    MarketData apply(const Bump& b) const {
        const auto colon = b.factor.find(':');
        const std::string kind = b.factor.substr(0, colon);
        const std::string name = colon == std::string::npos ? "" : b.factor.substr(colon + 1);
        MarketData out = *this;
        auto shifted = [&](double x) { return b.relative ? x * (1.0 + b.size) : x + b.size; };
        if (kind == "SPOT") out.spots.at(name) = shifted(spots.at(name));
        else if (kind == "VOL") out.vols.at(name) = vols.at(name) + b.size;
        else if (kind == "CURVE") out.curves.at(name).rate += b.size;
        else if (kind == "DIV") out.dividends[name].div_yield += b.size;
        else if (kind == "BORROW") out.dividends[name].borrow += b.size;
        else if (kind == "TIME") out = rolled(civil_from_days(days_from_civil(asof) + std::lround(b.size)));
        else throw std::invalid_argument("unknown risk factor " + b.factor);
        return out;
    }
};

struct EuropeanOption {
    std::string id, underlying, currency;
    double notional = 1.0;
    std::string discount_curve;
    double strike;
    Date expiry;
    bool call = true;
    bool american = false;
    std::string curve(const MarketData& md) const {
        if (!discount_curve.empty()) return discount_curve;
        if (md.curves.count(currency)) return currency;
        if (md.curves.size() == 1) return md.curves.begin()->first;
        throw std::invalid_argument(id + ": no discount curve");
    }
};

inline double intrinsic(const EuropeanOption& o, double s) { return std::max(o.call ? s - o.strike : o.strike - s, 0.0); }

struct AnalyticEngine {
    double price(const EuropeanOption& o, const MarketData& md) const {
        if (o.american) throw std::invalid_argument("the analytic engine prices European exercise only");
        const double t = md.t(o.expiry);
        if (t < 0) return 0.0;
        return o.notional * firm::bs::black(md.forward(o.underlying, o.expiry), o.strike, t, md.df(o.curve(md), o.expiry),
                                            md.vols.at(o.underlying), o.call ? firm::bs::Right::Call : firm::bs::Right::Put);
    }
};

inline std::vector<double> thomas(std::vector<double> a, std::vector<double> b, std::vector<double> c, std::vector<double> d) {
    const std::size_t n = d.size();
    std::vector<double> cp(n), dp(n), out(n);
    cp[0] = c[0] / b[0];
    dp[0] = d[0] / b[0];
    for (std::size_t i = 1; i < n; ++i) {
        const double m = b[i] - a[i] * cp[i - 1];
        cp[i] = c[i] / m;
        dp[i] = (d[i] - a[i] * dp[i - 1]) / m;
    }
    out[n - 1] = dp[n - 1];
    for (std::size_t i = n - 1; i-- > 0;) out[i] = dp[i] - cp[i] * out[i + 1];
    return out;
}

// Brennan-Schwartz with V >= g: exercise region at low spots (put); the call is the mirror image.
inline std::vector<double> projected(std::vector<double> a, std::vector<double> b, std::vector<double> c,
                                     std::vector<double> d, std::vector<double> g, bool put) {
    if (!put) {
        std::reverse(a.begin(), a.end());
        std::reverse(b.begin(), b.end());
        std::reverse(c.begin(), c.end());
        std::reverse(d.begin(), d.end());
        std::reverse(g.begin(), g.end());
        std::vector<double> out = projected(c, b, a, d, g, true);
        std::reverse(out.begin(), out.end());
        return out;
    }
    const std::size_t n = d.size();
    std::vector<double> bp(n), dp(n), out(n);
    bp[n - 1] = b[n - 1];
    dp[n - 1] = d[n - 1];
    for (std::size_t k = n - 1; k-- > 0;) {
        const double f = c[k] / bp[k + 1];
        bp[k] = b[k] - f * a[k + 1];
        dp[k] = d[k] - f * dp[k + 1];
    }
    out[0] = std::max(dp[0] / bp[0], g[0]);
    for (std::size_t i = 1; i < n; ++i) out[i] = std::max((dp[i] - a[i] * out[i - 1]) / bp[i], g[i]);
    return out;
}

// Crank-Nicolson in log-spot, uniform grid of m + 1 nodes, Rannacher start-up, Thomas or Brennan-Schwartz.
inline double fd_vanilla(double s0, double k, double t, double r, double q, double vol, bool call, bool american,
                         int m = 200, int n_t = 200, int rannacher = 2, double width = 5.0) {
    const double half = width * vol * std::sqrt(t);
    std::vector<double> x(m + 1), s(m + 1), g(m + 1), v(m + 1);
    const double sign = call ? 1.0 : -1.0;
    for (int i = 0; i <= m; ++i) {
        x[i] = std::log(s0) - half + 2.0 * half * i / m;
        s[i] = std::exp(x[i]);
        g[i] = std::max(sign * (s[i] - k), 0.0);
        v[i] = g[i];
    }
    const double nu = r - q - 0.5 * vol * vol, d2 = vol * vol;
    const int ni = m - 1;
    std::vector<double> lo(ni), di(ni), up(ni);
    for (int i = 1; i < m; ++i) {
        const double hm = x[i] - x[i - 1], hp = x[i + 1] - x[i];
        lo[i - 1] = d2 / (hm * (hm + hp)) - nu * hp / (hm * (hm + hp));
        di[i - 1] = -d2 / (hm * hp) + nu * (hp - hm) / (hm * hp) - r;
        up[i - 1] = d2 / (hp * (hm + hp)) + nu * hm / (hp * (hm + hp));
    }
    const double dt = t / n_t;
    double tau = 0.0;
    int step = 0, implicit_half = 2 * rannacher;
    const std::vector<double> gi(g.begin() + 1, g.end() - 1);
    while (step < n_t) {
        double h = dt, theta = 0.5;
        if (implicit_half > 0) {
            h = 0.5 * dt;
            theta = 1.0;
            --implicit_half;
        }
        tau += h;
        std::vector<double> a(ni), b(ni), c(ni), rhs(ni);
        for (int i = 0; i < ni; ++i) {
            rhs[i] = v[i + 1] + (1 - theta) * h * (lo[i] * v[i] + di[i] * v[i + 1] + up[i] * v[i + 2]);
            a[i] = -theta * h * lo[i];
            b[i] = 1 - theta * h * di[i];
            c[i] = -theta * h * up[i];
        }
        double e0 = std::max(sign * (s[0] * std::exp(-q * tau) - k * std::exp(-r * tau)), 0.0);
        double e1 = std::max(sign * (s[m] * std::exp(-q * tau) - k * std::exp(-r * tau)), 0.0);
        if (american) {
            e0 = std::max(e0, g[0]);
            e1 = std::max(e1, g[m]);
        }
        rhs[0] -= a[0] * e0;
        rhs[ni - 1] -= c[ni - 1] * e1;
        a[0] = 0.0;
        c[ni - 1] = 0.0;
        const std::vector<double> inner = american ? projected(a, b, c, rhs, gi, !call) : thomas(a, b, c, rhs);
        v[0] = e0;
        v[m] = e1;
        for (int i = 0; i < ni; ++i) v[i + 1] = inner[i];
        if (std::fabs(tau - (step + 1) * dt) < 1e-12 * std::max(1.0, t)) ++step;
    }
    const double x0 = std::log(s0);
    int i = m;
    for (int j = 0; j <= m; ++j)
        if (x[j] >= x0) {
            i = j;
            break;
        }
    i = std::clamp(i, 1, m - 1);
    const double x1 = x[i - 1], x2 = x[i], x3 = x[i + 1];
    return v[i - 1] * (x0 - x2) * (x0 - x3) / ((x1 - x2) * (x1 - x3)) + v[i] * (x0 - x1) * (x0 - x3) / ((x2 - x1) * (x2 - x3)) +
           v[i + 1] * (x0 - x1) * (x0 - x2) / ((x3 - x1) * (x3 - x2));
}

struct PDEEngine {
    int m = 200, n_t = 200;
    double price(const EuropeanOption& o, const MarketData& md) const {
        const double t = md.t(o.expiry);
        const double s = md.spots.at(o.underlying);
        if (t <= 0) return t == 0 ? o.notional * intrinsic(o, s) : 0.0;
        const std::string fc = md.funding_curve(o.underlying);
        const double r = -std::log(md.df(fc, o.expiry)) / t;
        const double q = r - std::log(md.forward(o.underlying, o.expiry) / s) / t;
        const double v = fd_vanilla(s, o.strike, t, r, q, md.vols.at(o.underlying), o.call, o.american, m, n_t);
        return o.notional * v * md.df(o.curve(md), o.expiry) / md.df(fc, o.expiry);
    }
};

struct Greeks {
    double delta, gamma, vega, theta, rho;
};

// Desk units as firm_pricing.greeks: delta per unit of spot, gamma per 1 % (Gamma S^2 / 100), vega per volatility
// point, theta per day, rho per basis point on every curve.
template <class Engine>
Greeks greeks(const EuropeanOption& o, const MarketData& md, const Engine& e, double h = 0.01) {
    const double s = md.spots.at(o.underlying);
    const double base = e.price(o, md);
    const double up = e.price(o, md.apply({"SPOT:" + o.underlying, h, true}));
    const double dn = e.price(o, md.apply({"SPOT:" + o.underlying, -h, true}));
    Greeks g{};
    g.delta = (up - dn) / (2 * h * s);
    g.gamma = (up - 2 * base + dn) / ((h * s) * (h * s)) * s * s / 100.0;
    g.vega = (e.price(o, md.apply({"VOL:" + o.underlying, 0.01})) - e.price(o, md.apply({"VOL:" + o.underlying, -0.01}))) / 2;
    g.theta = e.price(o, md.rolled(civil_from_days(days_from_civil(md.asof) + 1))) - base;
    MarketData cu = md, cd = md;
    for (auto& [name, c] : cu.curves) c.rate += 1e-4;
    for (auto& [name, c] : cd.curves) c.rate -= 1e-4;
    g.rho = (e.price(o, cu) - e.price(o, cd)) / 2;
    return g;
}

}  // namespace firm::pricing
