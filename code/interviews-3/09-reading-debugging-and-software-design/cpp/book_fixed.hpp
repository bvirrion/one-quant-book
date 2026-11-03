#pragma once
#include <algorithm>
#include <list>
#include <map>
#include <unordered_map>

struct Order { long id; long qty; };

template <class Better>                      // std::less for asks, std::greater for bids
class Side {
public:
    void add(long price, long id, long qty) {
        auto& level = levels_[price];
        level.push_back({id, qty});
        index_[id] = {price, std::prev(level.end())};   // list iterators survive growth
    }
    bool cancel(long id) {
        auto it = index_.find(id);
        if (it == index_.end()) return false;
        auto level = levels_.find(it->second.price);
        level->second.erase(it->second.where);
        if (level->second.empty()) levels_.erase(level);
        index_.erase(it);
        return true;
    }
    long take(long qty) {
        long filled = 0;
        for (auto it = levels_.begin(); it != levels_.end() && filled < qty;) {
            auto& level = it->second;
            while (!level.empty() && filled < qty) {
                Order& o = level.front();
                const long n = std::min(o.qty, qty - filled);
                o.qty -= n;
                filled += n;
                if (o.qty == 0) { index_.erase(o.id); level.pop_front(); }
            }
            it = level.empty() ? levels_.erase(it) : std::next(it);
        }
        return filled;
    }
    bool empty() const { return levels_.empty(); }
    long best() const { return levels_.begin()->first; }

private:
    struct Where { long price; std::list<Order>::iterator where; };
    std::map<long, std::list<Order>, Better> levels_;
    std::unordered_map<long, Where> index_;
};
