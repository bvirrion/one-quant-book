// Book 18, chapter 21: five of the algorithm answers in C++20.
#pragma once
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <deque>
#include <functional>
#include <map>
#include <optional>
#include <queue>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

namespace iv {

// Maximum of each window of k consecutive prices: a deque of indices with decreasing prices.
inline std::vector<std::int64_t> sliding_max(const std::vector<std::int64_t>& p, std::size_t k) {
    std::deque<std::size_t> dq;
    std::vector<std::int64_t> out;
    for (std::size_t i = 0; i < p.size(); ++i) {
        while (!dq.empty() && p[dq.back()] <= p[i]) dq.pop_back();
        dq.push_back(i);
        if (dq.front() + k <= i) dq.pop_front();
        if (i + 1 >= k) out.push_back(p[dq.front()]);
    }
    return out;
}

// Largest number of orders open at once; an order is open on [start, end).
inline int max_open(const std::vector<std::pair<int, int>>& orders) {
    std::vector<std::pair<int, int>> ev;
    for (auto [s, e] : orders) {
        ev.emplace_back(s, +1);
        ev.emplace_back(e, -1);
    }
    std::sort(ev.begin(), ev.end());  // at equal times -1 (an end) sorts before +1
    int cur = 0, best = 0;
    for (auto [t, d] : ev) best = std::max(best, cur += d);
    return best;
}

// The k symbols with the largest total volume.
inline std::vector<std::string> top_k(const std::vector<std::pair<std::string, std::int64_t>>& trades,
                                      std::size_t k) {
    std::unordered_map<std::string, std::int64_t> tot;
    for (const auto& [s, v] : trades) tot[s] += v;
    using Item = std::pair<std::int64_t, std::string>;
    std::priority_queue<Item, std::vector<Item>, std::greater<>> heap;  // min-heap of the best k so far
    for (const auto& [s, v] : tot) {
        heap.emplace(v, s);
        if (heap.size() > k) heap.pop();
    }
    std::vector<std::string> out;
    while (!heap.empty()) {
        out.push_back(heap.top().second);
        heap.pop();
    }
    std::reverse(out.begin(), out.end());
    return out;
}

// One side of a book aggregated by price: O(log n) add, cancel and best.
class PriceLevels {
public:
    explicit PriceLevels(bool bid) : bid_(bid) {}
    void add(std::int64_t price, std::int64_t qty) { levels_[price] += qty; }
    void cancel(std::int64_t price, std::int64_t qty) {
        auto it = levels_.find(price);
        if (it == levels_.end()) return;
        if ((it->second -= qty) <= 0) levels_.erase(it);
    }
    std::optional<std::int64_t> best() const {
        if (levels_.empty()) return std::nullopt;
        return bid_ ? levels_.rbegin()->first : levels_.begin()->first;
    }

private:
    bool bid_;
    std::map<std::int64_t, std::int64_t> levels_;
};

// True if a cycle of conversions multiplies money: Bellman-Ford on -log(rate).
inline bool arbitrage_cycle(const std::vector<std::vector<double>>& rate) {
    const std::size_t n = rate.size();
    std::vector<double> dist(n, 0.0);
    auto relax = [&](bool update) {
        bool changed = false;
        for (std::size_t i = 0; i < n; ++i)
            for (std::size_t j = 0; j < n; ++j) {
                if (rate[i][j] <= 0) continue;
                const double w = -std::log(rate[i][j]);
                if (dist[i] + w < dist[j] - 1e-12) {
                    changed = true;
                    if (update) dist[j] = dist[i] + w;
                }
            }
        return changed;
    };
    for (std::size_t r = 0; r + 1 < n; ++r) relax(true);
    return relax(false);
}

}  // namespace iv
