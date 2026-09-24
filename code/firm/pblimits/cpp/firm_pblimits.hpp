#pragma once
// firm.pblimits -- pre-trade prime-broker limit gate (build of Chapter 27, One Quant Book 2), C++20.
// Each prime broker's notice gives allowed pairs, a maximum tenor, a net open position (NOP) limit and
// a settlement limit per value date. NOP = sum of net long USD values across currencies; settlement
// of a value date = sum of USD values of currencies to be received. An order passes if it keeps both
// within limits or does not increase one already above its limit. Twin of firm_pblimits.py.
#include <algorithm>
#include <map>
#include <optional>
#include <set>
#include <string>
#include <vector>

namespace firm::pblimits {

struct Limits {
    std::string pb;
    double fee_per_m, nop_limit, settle_limit;
    int max_tenor;
    std::set<std::string> pairs;
};

struct Order {
    std::string pair;   // base then quote, e.g. "EURUSD"
    bool buy;           // buy the base currency
    double amount;      // base currency
    double rate;        // quote per base
    int value_day;
};

using Usd = std::map<std::string, double>;
enum class Decision { ok, pair, tenor, nop, settlement };

inline double positive_sum(const Usd& m) {
    double s = 0.0;
    for (const auto& [c, v] : m) if (v > 0) s += v;
    return s;
}

inline Usd legs(const Order& o, const Usd& usd_per) {
    const std::string base = o.pair.substr(0, 3), quote = o.pair.substr(3, 3);
    const double sign = o.buy ? 1.0 : -1.0;
    return {{base, sign * o.amount * usd_per.at(base)}, {quote, -sign * o.amount * o.rate * usd_per.at(quote)}};
}

class Book {
public:
    explicit Book(Limits l) : limits(std::move(l)) {}
    Limits limits;
    Usd net;
    std::map<int, Usd> settle;

    double nop() const { return positive_sum(net); }
    double settlement(int day) const {
        auto it = settle.find(day);
        return it == settle.end() ? 0.0 : positive_sum(it->second);
    }

    Decision check(const Order& o, const Usd& usd_per) const {
        if (!limits.pairs.contains(o.pair)) return Decision::pair;
        if (o.value_day > limits.max_tenor) return Decision::tenor;
        Usd n = net, f;
        if (auto it = settle.find(o.value_day); it != settle.end()) f = it->second;
        for (const auto& [c, v] : legs(o, usd_per)) { n[c] += v; f[c] += v; }
        const double new_nop = positive_sum(n), new_set = positive_sum(f);
        if (new_nop > limits.nop_limit && new_nop > nop()) return Decision::nop;
        if (new_set > limits.settle_limit && new_set > settlement(o.value_day)) return Decision::settlement;
        return Decision::ok;
    }

    void apply(const Order& o, const Usd& usd_per) {
        Usd& day = settle[o.value_day];
        for (const auto& [c, v] : legs(o, usd_per)) { net[c] += v; day[c] += v; }
    }
};

// Give the order up to the cheapest prime broker that accepts it.
inline std::optional<std::string> route(std::vector<Book>& books, const Order& o, const Usd& usd_per) {
    std::vector<Book*> order;
    for (auto& b : books) order.push_back(&b);
    std::sort(order.begin(), order.end(), [](Book* a, Book* b) { return a->limits.fee_per_m < b->limits.fee_per_m; });
    for (Book* b : order)
        if (b->check(o, usd_per) == Decision::ok) { b->apply(o, usd_per); return b->limits.pb; }
    return std::nullopt;
}

}  // namespace firm::pblimits
