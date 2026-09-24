#pragma once
// firm.auction -- call-auction uncrossing (build of Chapter 13, One Quant Book 1), C++20.
// Same four rules as the Python reference: volume, surplus, market pressure, reference price.
#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <optional>
#include <set>
#include <string>
#include <tuple>
#include <utility>
#include <vector>

namespace firm {

struct AuctionOrder {
    std::string id;
    int side;                           // +1 buy, -1 sell
    std::int64_t quantity;
    std::optional<std::int64_t> price;  // nullopt = market order
    std::int64_t seq;                   // time priority
};

struct Uncrossing {
    std::optional<std::int64_t> price;
    std::int64_t volume = 0;
    std::int64_t surplus = 0;           // + buy interest left at the price, - sell
    std::vector<std::pair<std::string, std::int64_t>> fills;
};

inline std::int64_t abs64(std::int64_t x) { return x < 0 ? -x : x; }

inline std::int64_t interest(const std::vector<AuctionOrder>& orders, int side, std::int64_t p) {
    std::int64_t q = 0;
    for (const auto& o : orders)
        if (o.side == side && (!o.price || (side > 0 ? *o.price >= p : *o.price <= p))) q += o.quantity;
    return q;
}

inline Uncrossing uncross(const std::vector<AuctionOrder>& orders, std::int64_t reference) {
    std::set<std::int64_t> prices{reference};
    for (const auto& o : orders) if (o.price) prices.insert(*o.price);
    struct Row { std::int64_t p, d, s; };
    std::vector<Row> rows;
    std::int64_t best = 0;
    for (auto p : prices) {
        rows.push_back({p, interest(orders, +1, p), interest(orders, -1, p)});
        best = std::max(best, std::min(rows.back().d, rows.back().s));
    }
    if (best == 0) return {};
    std::erase_if(rows, [&](const Row& r) { return std::min(r.d, r.s) != best; });            // rule 1
    std::int64_t least = INT64_MAX;
    for (const auto& r : rows) least = std::min(least, abs64(r.d - r.s));
    std::erase_if(rows, [&](const Row& r) { return abs64(r.d - r.s) != least; });        // rule 2
    const bool all_buy = std::all_of(rows.begin(), rows.end(), [](const Row& r) { return r.d > r.s; });
    const bool all_sell = std::all_of(rows.begin(), rows.end(), [](const Row& r) { return r.d < r.s; });
    Row pick = rows.front();
    if (all_buy) pick = rows.back();                                                           // rule 3
    else if (!all_sell)
        pick = *std::min_element(rows.begin(), rows.end(), [&](const Row& a, const Row& b) {    // rule 4
            return std::pair(abs64(a.p - reference), a.p) < std::pair(abs64(b.p - reference), b.p);
        });
    Uncrossing u{pick.p, best, pick.d - pick.s, {}};
    for (int side : {+1, -1}) {
        std::vector<const AuctionOrder*> el;
        for (const auto& o : orders)
            if (o.side == side && (!o.price || (side > 0 ? *o.price >= pick.p : *o.price <= pick.p))) el.push_back(&o);
        std::sort(el.begin(), el.end(), [&](const AuctionOrder* a, const AuctionOrder* b) {
            const auto key = [&](const AuctionOrder* o) {
                return std::tuple(o->price.has_value(), -side * o->price.value_or(0), o->seq);
            };
            return key(a) < key(b);
        });
        std::int64_t left = best;
        for (const auto* o : el) {
            const std::int64_t q = std::min(left, o->quantity);
            if (q > 0) u.fills.emplace_back(o->id, q);
            left -= q;
        }
    }
    return u;
}

}  // namespace firm
