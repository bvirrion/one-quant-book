#pragma once
// firm.bond -- fixed-coupon government bonds (build of Chapter 3, One Quant Book 2), C++20.
// Twin of firm_bond.py: schedule back from maturity (end-of-month rule), actual/actual accrued
// interest, street and Treasury price conventions, yield by Newton, duration, DV01, convexity.
#include <chrono>
#include <cmath>
#include <stdexcept>
#include <vector>

namespace firm::bond {

using std::chrono::day;
using std::chrono::days;
using std::chrono::month;
using std::chrono::months;
using std::chrono::sys_days;
using std::chrono::year_month_day;
using std::chrono::year_month_day_last;

inline bool is_month_end(year_month_day d) {
    return year_month_day{year_month_day_last{d.year(), std::chrono::month_day_last{d.month()}}} == d;
}

inline year_month_day add_months(year_month_day d, int n, bool eom) {
    const auto ym = std::chrono::year_month{d.year(), d.month()} + months{n};
    const year_month_day last{year_month_day_last{ym.year(), std::chrono::month_day_last{ym.month()}}};
    if (eom || d.day() > last.day()) return last;
    return year_month_day{ym.year(), ym.month(), d.day()};
}

inline int days_between(year_month_day a, year_month_day b) {
    return static_cast<int>((sys_days{b} - sys_days{a}).count());
}

struct Risk { double dirty, macaulay, modified, dv01, convexity; };

struct Bond {
    double coupon;            // annual, percent of face
    year_month_day maturity;
    int freq = 2;

    // Previous coupon date, next coupon date and the number of coupons left after settle.
    void locate(year_month_day settle, year_month_day& prev, year_month_day& next, int& n) const {
        const bool eom = is_month_end(maturity);
        const int step = 12 / freq;
        n = 0;
        year_month_day d = maturity;
        next = maturity;
        while (sys_days{d} > sys_days{settle}) {
            next = d;
            ++n;
            d = add_months(maturity, -step * n, eom);
        }
        prev = d;
    }

    double fraction_to_next(year_month_day settle, int& n) const {
        year_month_day prev, next;
        locate(settle, prev, next, n);
        return static_cast<double>(days_between(settle, next)) / days_between(prev, next);
    }

    double accrued(year_month_day settle) const {
        int n = 0;
        return coupon / freq * (1.0 - fraction_to_next(settle, n));
    }

    double dirty_price(double y, year_month_day settle, bool treasury = false) const {
        int n = 0;
        const double w = fraction_to_next(settle, n);
        const double c = coupon / freq, v = 1.0 / (1.0 + y / freq);
        double at_next = 100.0 * std::pow(v, n - 1), vk = 1.0;   // value at the next coupon date
        for (int k = 0; k < n; ++k, vk *= v) at_next += c * vk;
        return treasury ? at_next / (1.0 + w * y / freq) : at_next * std::pow(v, w);
    }

    double clean_price(double y, year_month_day settle, bool treasury = false) const {
        return dirty_price(y, settle, treasury) - accrued(settle);
    }

    double yield_from_clean(double clean, year_month_day settle) const {
        double y = coupon / 100.0;
        for (int i = 0; i < 100; ++i) {
            const double h = 1e-7;
            const double f = clean_price(y, settle) - clean;
            const double df = (clean_price(y + h, settle) - clean_price(y - h, settle)) / (2 * h);
            const double step = f / df;
            y -= step;
            if (std::fabs(step) < 1e-12) return y;
        }
        throw std::runtime_error("yield did not converge");
    }

    Risk risk(double y, year_month_day settle) const {
        int n = 0;
        const double w = fraction_to_next(settle, n);
        const double c = coupon / freq, v = 1.0 / (1.0 + y / freq);
        double p = 0.0, t1 = 0.0, t2 = 0.0;
        for (int k = 0; k < n; ++k) {
            const double t = k + w;                                  // periods to the flow
            const double pv = (c + (k == n - 1 ? 100.0 : 0.0)) * std::pow(v, t);
            p += pv;
            t1 += t * pv;
            t2 += t * (t + 1.0) * pv;
        }
        const double mac = t1 / p / freq, mod = mac / (1.0 + y / freq);
        const double conv = t2 / p / (freq * freq) / ((1.0 + y / freq) * (1.0 + y / freq));
        return {p, mac, mod, p * mod * 1e-4, conv};
    }
};

}  // namespace firm::bond
