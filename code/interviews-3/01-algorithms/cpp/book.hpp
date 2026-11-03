#pragma once
#include <map>
#include <optional>
#include <unordered_map>

enum class Side { Bid, Ask };
struct Level { long qty = 0; long orders = 0; };
struct Top { long price; long qty; };

class Book {
public:
    bool add(long id, Side side, long price, long qty) {
        if (qty <= 0 || orders_.count(id)) return false;
        auto level = levels_[idx(side)].try_emplace(price).first;
        level->second.qty += qty;
        level->second.orders += 1;
        orders_.emplace(id, Order{side, qty, level});
        return true;
    }
    bool cancel(long id) {
        auto it = orders_.find(id);
        if (it == orders_.end()) return false;
        const Order& o = it->second;
        o.level->second.qty -= o.qty;
        if (--o.level->second.orders == 0) levels_[idx(o.side)].erase(o.level);
        orders_.erase(it);
        return true;
    }
    std::optional<Top> best_bid() const {
        return top(levels_[0].crbegin(), levels_[0].crend());
    }
    std::optional<Top> best_ask() const {
        return top(levels_[1].cbegin(), levels_[1].cend());
    }
private:
    using Levels = std::map<long, Level>;
    struct Order { Side side; long qty; Levels::iterator level; };
    static int idx(Side s) { return s == Side::Bid ? 0 : 1; }
    template <class It> static std::optional<Top> top(It first, It last) {
        if (first == last) return std::nullopt;
        return Top{first->first, first->second.qty};
    }
    Levels levels_[2];                         // price -> level; iterators survive inserts
    std::unordered_map<long, Order> orders_;   // id -> where the order sits
};
