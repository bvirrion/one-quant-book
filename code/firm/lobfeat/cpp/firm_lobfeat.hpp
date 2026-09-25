// firm.lobfeat -- streaming order-book features (One Quant Book 7, chapter 8), C++20 twin of firm_lobfeat.py.
// Same state, same operation order, same outputs (checked on data/fixture_*.csv).
#pragma once
#include <cstdint>
#include <functional>
#include <map>
#include <optional>
#include <unordered_map>
#include <vector>

namespace firm {

struct Features {
    std::int64_t bid, ask, bid_qty, ask_qty;
    double imbalance, depth_imbalance;
    std::int64_t ofi, ofi_cum;
    double wmid, micro;
};

inline int bucket(double imbalance, int n) {
    int b = static_cast<int>((imbalance + 1.0) / 2.0 * n);
    return b < n - 1 ? b : n - 1;
}

class LobFeatures {
  public:
    explicit LobFeatures(int levels = 5, std::vector<double> g = {}) : levels_(levels), g_(std::move(g)) {}

    std::optional<Features> on(char kind, std::int64_t oid, int side, std::int64_t price, std::int64_t qty) {
        auto apply = [&](auto& lv) {
            if (kind == 'A') {
                orders_[oid] = Order{side, price, qty};
                lv[price] += qty;
                return;
            }
            Order& o = orders_.at(oid);
            o.qty -= qty;
            lv[price] -= qty;
            if (o.qty == 0) orders_.erase(oid);
            if (lv[price] == 0) lv.erase(price);
        };
        if (side == 1) apply(bids_); else apply(asks_);
        if (bids_.empty() || asks_.empty()) return std::nullopt;
        const std::int64_t bb = bids_.begin()->first, qb = bids_.begin()->second;
        const std::int64_t ba = asks_.begin()->first, qa = asks_.begin()->second;
        std::int64_t e = 0;
        if (has_prev_) {
            e = (bb >= pb_ ? qb : 0) - (bb <= pb_ ? pqb_ : 0) - (ba <= pa_ ? qa : 0) + (ba >= pa_ ? pqa_ : 0);
        }
        has_prev_ = true;
        pb_ = bb, pqb_ = qb, pa_ = ba, pqa_ = qa;
        ofi_cum_ += e;
        const double imb = static_cast<double>(qb - qa) / static_cast<double>(qb + qa);
        const std::int64_t db = depth(bids_), da = depth(asks_);
        const double dimb = static_cast<double>(db - da) / static_cast<double>(db + da);
        const double mid = 0.5 * static_cast<double>(bb + ba);
        const double wmid = static_cast<double>(ba * qb + bb * qa) / static_cast<double>(qb + qa);
        double micro = mid;
        if (!g_.empty() && ba - bb == 1) micro = mid + g_[bucket(imb, static_cast<int>(g_.size()))];
        return Features{bb, ba, qb, qa, imb, dimb, e, ofi_cum_, wmid, micro};
    }

  private:
    struct Order { int side; std::int64_t price, qty; };
    template <class M> std::int64_t depth(const M& lv) const {
        std::int64_t s = 0;
        int k = 0;
        for (auto it = lv.begin(); it != lv.end() && k < levels_; ++it, ++k) s += it->second;
        return s;
    }

    int levels_;
    std::vector<double> g_;
    std::unordered_map<std::int64_t, Order> orders_;
    std::map<std::int64_t, std::int64_t, std::greater<>> bids_;   // best (highest) first
    std::map<std::int64_t, std::int64_t> asks_;                     // best (lowest) first
    bool has_prev_ = false;
    std::int64_t pb_ = 0, pqb_ = 0, pa_ = 0, pqa_ = 0, ofi_cum_ = 0;
};

}  // namespace firm
