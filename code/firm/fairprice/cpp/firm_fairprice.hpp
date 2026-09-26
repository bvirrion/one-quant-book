// firm.fairprice -- the fair-price filter (One Quant Book 11, chapter 2), C++20 twin of firm_fairprice.FairFilter.
// A local-level Kalman filter over irregular observations from several sources; same operation order as the Python
// reference, so both produce the same doubles on the shared fixture (data/fixture_*.csv).
#pragma once

#include <cmath>
#include <limits>
#include <optional>
#include <utility>
#include <vector>

namespace firm {

class FairFilter {
public:
    FairFilter(double q, std::vector<double> r) : q_(q), r_(std::move(r)) {}

    // Propagate the variance to time t, then update with observation y from source src; returns the estimate.
    double update(double t, std::size_t src, double y) {
        if (!t_) {
            t_ = t;
            x_ = y;
            p_ = r_[src];
            return x_;
        }
        p_ += q_ * (t - *t_);
        t_ = t;
        const double k = p_ / (p_ + r_[src]);
        x_ += k * (y - x_);
        p_ = (1.0 - k) * p_;
        return x_;
    }

    [[nodiscard]] double estimate() const { return x_; }
    [[nodiscard]] double variance() const { return p_; }

private:
    double q_;
    std::vector<double> r_;
    double x_ = std::numeric_limits<double>::quiet_NaN();
    double p_ = 1e6;
    std::optional<double> t_;
};

}  // namespace firm
