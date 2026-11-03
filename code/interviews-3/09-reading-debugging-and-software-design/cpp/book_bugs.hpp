#pragma once
#include <algorithm>
#include <map>
#include <unordered_map>
#include <vector>

struct Order { long id; long qty; };

class Side {                                 // used for both the bid side and the ask side
public:
    void add(long price, long id, long qty) {
        auto& level = levels_[price];
        level.push_back({id, qty});
        index_[id] = &level.back();
    }
    bool cancel(long id) {
        auto it = index_.find(id);
        if (it == index_.end()) return false;
        it->second->qty = 0;
        index_.erase(it);
        return true;
    }
    long take(long qty) {                    // best price first, oldest first
        long filled = 0;
        for (auto& [price, level] : levels_) {
            for (auto& o : level) {
                const long n = std::min(o.qty, qty - filled);
                o.qty -= n;
                filled += n;
                if (n > 0 && o.qty == 0) index_.erase(o.id);
            }
            if (spent(level)) levels_.erase(price);
            if (filled == qty) break;
        }
        return filled;
    }
    bool empty() const { return levels_.empty(); }
    long best() const { return levels_.begin()->first; }

private:
    static bool spent(const std::vector<Order>& level) {
        return std::ranges::all_of(level, [](const Order& o) { return o.qty == 0; });
    }
    std::map<long, std::vector<Order>> levels_;
    std::unordered_map<long, Order*> index_;
};
