// firm.lob (One Quant Book 10, chapter 1), C++20: the public book rebuilt from a market-by-order stream.
// Orders by reference in a hash map; each side a sorted map from price to the level's displayed size.
// Same semantics as firm_lob.MessageBook: A add, X/E/C reduce, D delete, U replace (new reference).
#pragma once
#include <cstdint>
#include <functional>
#include <map>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

namespace firm::lob {

struct Resting {
    int side;            // +1 bid, -1 ask
    std::int64_t price;
    std::int64_t qty;
};

class MessageBook {
public:
    void add(std::uint64_t ref, int side, std::int64_t price, std::int64_t qty) {
        if (!orders_.emplace(ref, Resting{side, price, qty}).second) throw std::runtime_error("duplicate reference");
        level(side)[price] += qty;
    }
    void reduce(std::uint64_t ref, std::int64_t qty) {
        auto it = orders_.find(ref);
        if (it == orders_.end()) throw std::runtime_error("unknown reference");
        Resting& o = it->second;
        if (qty <= 0 || qty > o.qty) throw std::runtime_error("bad reduce");
        take(o.side, o.price, qty);
        o.qty -= qty;
        if (o.qty == 0) orders_.erase(it);
    }
    void remove(std::uint64_t ref) {
        auto it = orders_.find(ref);
        if (it == orders_.end()) throw std::runtime_error("unknown reference");
        take(it->second.side, it->second.price, it->second.qty);
        orders_.erase(it);
    }
    void replace(std::uint64_t ref, std::uint64_t new_ref, std::int64_t price, std::int64_t qty) {
        auto it = orders_.find(ref);
        if (it == orders_.end()) throw std::runtime_error("unknown reference");
        const int side = it->second.side;
        remove(ref);
        add(new_ref, side, price, qty);
    }
    // Best `n` levels of one side, best first.
    std::vector<std::pair<std::int64_t, std::int64_t>> depth(int side, std::size_t n) const {
        std::vector<std::pair<std::int64_t, std::int64_t>> out;
        if (side == 1) {
            for (auto it = bids_.rbegin(); it != bids_.rend() && out.size() < n; ++it) out.emplace_back(it->first, it->second);
        } else {
            for (auto it = asks_.begin(); it != asks_.end() && out.size() < n; ++it) out.emplace_back(it->first, it->second);
        }
        return out;
    }
    std::size_t live() const { return orders_.size(); }

private:
    std::map<std::int64_t, std::int64_t>& level(int side) { return side == 1 ? bids_ : asks_; }
    void take(int side, std::int64_t price, std::int64_t qty) {
        auto& lv = level(side);
        auto it = lv.find(price);
        it->second -= qty;
        if (it->second == 0) lv.erase(it);
    }
    std::unordered_map<std::uint64_t, Resting> orders_;
    std::map<std::int64_t, std::int64_t> bids_, asks_;
};

// The canonical two-line text of firm_lob.l2_lines.
inline std::string l2_lines(const MessageBook& b, std::size_t n) {
    std::string s = "B";
    for (auto [p, q] : b.depth(1, n)) s += " " + std::to_string(p) + ":" + std::to_string(q);
    s += "\nS";
    for (auto [p, q] : b.depth(-1, n)) s += " " + std::to_string(p) + ":" + std::to_string(q);
    return s;
}

}  // namespace firm::lob
