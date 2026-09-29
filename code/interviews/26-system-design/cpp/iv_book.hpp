// Book 18, chapter 26: a price-time priority matching core in C++20 (limit orders, cancels).
#pragma once
#include <algorithm>
#include <cstdint>
#include <functional>
#include <list>
#include <map>
#include <optional>
#include <unordered_map>
#include <vector>

namespace iv {

enum class Side { Buy, Sell };

struct Fill {
    std::uint64_t maker, taker;
    std::int64_t price, qty;
    bool operator==(const Fill&) const = default;
};

class Book {
    struct Resting {
        std::uint64_t id;
        std::int64_t qty;
    };
    using Level = std::list<Resting>;  // FIFO within a price level
    std::map<std::int64_t, Level, std::greater<>> bids_;
    std::map<std::int64_t, Level> asks_;
    struct Where {
        Side side;
        std::int64_t price;
        Level::iterator it;
    };
    std::unordered_map<std::uint64_t, Where> index_;  // order id -> position, for O(1) cancel

    template <typename Opp>
    void match(Opp& opp, std::uint64_t id, std::int64_t price, std::int64_t& qty, bool buy,
               std::vector<Fill>& out) {
        while (qty > 0 && !opp.empty()) {
            auto lvl = opp.begin();
            if (buy ? lvl->first > price : lvl->first < price) break;  // no longer crosses
            auto& q = lvl->second;
            while (qty > 0 && !q.empty()) {
                auto& maker = q.front();
                const std::int64_t n = std::min(qty, maker.qty);
                out.push_back({maker.id, id, lvl->first, n});
                qty -= n;
                if ((maker.qty -= n) == 0) {
                    index_.erase(maker.id);
                    q.pop_front();
                }
            }
            if (q.empty()) opp.erase(lvl);
        }
    }

public:
    std::vector<Fill> add(std::uint64_t id, Side side, std::int64_t price, std::int64_t qty) {
        std::vector<Fill> out;
        if (side == Side::Buy) match(asks_, id, price, qty, true, out);
        else match(bids_, id, price, qty, false, out);
        if (qty > 0) {  // the remainder rests at its limit, behind earlier orders at that price
            if (side == Side::Buy) {
                auto& q = bids_[price];
                index_[id] = {side, price, q.insert(q.end(), {id, qty})};
            } else {
                auto& q = asks_[price];
                index_[id] = {side, price, q.insert(q.end(), {id, qty})};
            }
        }
        return out;
    }
    bool cancel(std::uint64_t id) {
        auto f = index_.find(id);
        if (f == index_.end()) return false;
        auto [side, price, it] = f->second;
        if (side == Side::Buy) {
            auto& q = bids_[price];
            q.erase(it);
            if (q.empty()) bids_.erase(price);
        } else {
            auto& q = asks_[price];
            q.erase(it);
            if (q.empty()) asks_.erase(price);
        }
        index_.erase(f);
        return true;
    }
    std::optional<std::int64_t> best_bid() const {
        return bids_.empty() ? std::nullopt : std::optional{bids_.begin()->first};
    }
    std::optional<std::int64_t> best_ask() const {
        return asks_.empty() ? std::nullopt : std::optional{asks_.begin()->first};
    }
};

}  // namespace iv
