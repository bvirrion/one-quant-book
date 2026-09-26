// Chapter 19: two textbook book builders the ladder is measured against -- a tree map of levels with a hash map of
// orders, and a sorted vector of levels -- with the ladder's interface (apply, depth).
#pragma once
#include <algorithm>
#include <cstdint>
#include <functional>
#include <map>
#include <unordered_map>
#include <vector>

#include "../../../firm/bookbuilder/cpp/firm_bookbuilder.hpp"

namespace ll::books {

using firm::feed2::Event;

struct Order {
    std::uint32_t price;
    std::uint64_t qty;
    std::uint8_t side;
};

// Levels in a balanced tree per side (std::map: a node allocated per new price level).
class TreeBook {
public:
    void apply(const Event& e) {
        switch (e.kind) {
            case 'A': add(e.ref, e.side, e.price, e.qty); break;
            case 'E': case 'X': case 'C': reduce(e.ref, e.qty); break;
            case 'D': if (auto it = orders_.find(e.ref); it != orders_.end()) reduce(e.ref, it->second.qty); break;
            case 'U':
                if (auto it = orders_.find(e.ref); it != orders_.end()) {
                    const auto side = it->second.side;
                    reduce(e.ref, it->second.qty);
                    add(e.ref2, side, e.price, e.qty);
                }
                break;
            case 'G': orders_.clear(); bids_.clear(); asks_.clear(); break;
            default: break;
        }
    }
    std::size_t depth(std::uint8_t side, std::size_t n, std::uint32_t* p, std::uint64_t* q) const {
        std::size_t k = 0;
        if (side == 'B')
            for (auto it = bids_.rbegin(); it != bids_.rend() && k < n; ++it, ++k) { p[k] = it->first; q[k] = it->second; }
        else
            for (auto it = asks_.begin(); it != asks_.end() && k < n; ++it, ++k) { p[k] = it->first; q[k] = it->second; }
        return k;
    }

private:
    void add(std::uint64_t ref, std::uint8_t side, std::uint32_t price, std::uint64_t qty) {
        orders_[ref] = Order{price, qty, side};
        (side == 'B' ? bids_ : asks_)[price] += qty;
    }
    void reduce(std::uint64_t ref, std::uint64_t qty) {
        auto it = orders_.find(ref);
        if (it == orders_.end()) return;
        auto& o = it->second;
        qty = std::min(qty, o.qty);
        auto& lv = o.side == 'B' ? bids_ : asks_;
        auto l = lv.find(o.price);
        l->second -= qty;
        if (l->second == 0) lv.erase(l);
        o.qty -= qty;
        if (o.qty == 0) orders_.erase(it);
    }
    std::unordered_map<std::uint64_t, Order> orders_;
    std::map<std::uint32_t, std::uint64_t> bids_, asks_;
};

// Levels in a vector sorted best first: a change at the touch is at the front, but inserting a new level shifts
// everything behind it.
class VecBook {
public:
    VecBook() { bids_.reserve(1 << 14); asks_.reserve(1 << 14); orders_.reserve(1 << 16); }
    void apply(const Event& e) {
        switch (e.kind) {
            case 'A': add(e.ref, e.side, e.price, e.qty); break;
            case 'E': case 'X': case 'C': reduce(e.ref, e.qty); break;
            case 'D': if (auto it = orders_.find(e.ref); it != orders_.end()) reduce(e.ref, it->second.qty); break;
            case 'U':
                if (auto it = orders_.find(e.ref); it != orders_.end()) {
                    const auto side = it->second.side;
                    reduce(e.ref, it->second.qty);
                    add(e.ref2, side, e.price, e.qty);
                }
                break;
            case 'G': orders_.clear(); bids_.clear(); asks_.clear(); break;
            default: break;
        }
    }
    std::size_t depth(std::uint8_t side, std::size_t n, std::uint32_t* p, std::uint64_t* q) const {
        const auto& v = side == 'B' ? bids_ : asks_;
        std::size_t k = 0;
        for (; k < n && k < v.size(); ++k) { p[k] = v[k].first; q[k] = v[k].second; }
        return k;
    }

private:
    using Lv = std::vector<std::pair<std::uint32_t, std::uint64_t>>;
    static Lv::iterator find(Lv& v, std::uint8_t side, std::uint32_t price) {
        return side == 'B' ? std::lower_bound(v.begin(), v.end(), price, [](const auto& a, std::uint32_t x) { return a.first > x; })
                           : std::lower_bound(v.begin(), v.end(), price, [](const auto& a, std::uint32_t x) { return a.first < x; });
    }
    void add(std::uint64_t ref, std::uint8_t side, std::uint32_t price, std::uint64_t qty) {
        orders_[ref] = Order{price, qty, side};
        auto& v = side == 'B' ? bids_ : asks_;
        auto it = find(v, side, price);
        if (it != v.end() && it->first == price) it->second += qty;
        else v.insert(it, {price, qty});
    }
    void reduce(std::uint64_t ref, std::uint64_t qty) {
        auto it = orders_.find(ref);
        if (it == orders_.end()) return;
        auto& o = it->second;
        qty = std::min(qty, o.qty);
        auto& v = o.side == 'B' ? bids_ : asks_;
        auto l = find(v, o.side, o.price);
        l->second -= qty;
        if (l->second == 0) v.erase(l);
        o.qty -= qty;
        if (o.qty == 0) orders_.erase(it);
    }
    std::unordered_map<std::uint64_t, Order> orders_;
    Lv bids_, asks_;
};

}  // namespace ll::books
