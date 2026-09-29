// Tests for iv_algos.hpp: fixed examples and randomised comparisons with brute force (fixed seeds).
#include <cassert>
#include <cstdio>
#include <random>
#include <set>

#include "iv_algos.hpp"

static std::vector<std::int64_t> brute_sliding_max(const std::vector<std::int64_t>& p, std::size_t k) {
    std::vector<std::int64_t> out;
    for (std::size_t i = 0; i + k <= p.size(); ++i) out.push_back(*std::max_element(p.begin() + i, p.begin() + i + k));
    return out;
}

static int brute_max_open(const std::vector<std::pair<int, int>>& o) {
    int best = 0;
    for (const auto& [s0, e0] : o) {
        (void)e0;
        int c = 0;
        for (const auto& [s, e] : o) c += (s <= s0 && s0 < e);
        best = std::max(best, c);
    }
    return best;
}

int main() {
    assert((iv::sliding_max({4, 2, 12, 3, 8, 1}, 3) == std::vector<std::int64_t>{12, 12, 12, 8}));
    assert(iv::max_open({{0, 5}, {1, 3}, {3, 6}, {5, 7}}) == 2);
    assert((iv::top_k({{"A", 5}, {"B", 9}, {"A", 7}, {"C", 3}, {"C", 8}}, 2) == std::vector<std::string>{"A", "C"}));

    std::mt19937 rng(20260929);
    for (int trial = 0; trial < 500; ++trial) {
        std::vector<std::int64_t> p(1 + rng() % 30);
        for (auto& x : p) x = static_cast<std::int64_t>(rng() % 10);
        const std::size_t k = 1 + rng() % p.size();
        assert(iv::sliding_max(p, k) == brute_sliding_max(p, k));

        std::vector<std::pair<int, int>> o(1 + rng() % 12);
        for (auto& [s, e] : o) {
            s = static_cast<int>(rng() % 20);
            e = s + 1 + static_cast<int>(rng() % 8);
        }
        assert(iv::max_open(o) == brute_max_open(o));

        const bool bid = rng() % 2 == 0;
        iv::PriceLevels side(bid);
        std::map<std::int64_t, std::int64_t> book;
        for (int step = 0; step < 60; ++step) {
            const std::int64_t price = 90 + static_cast<std::int64_t>(rng() % 21);
            if (book[price] > 0 && rng() % 5 < 2) {
                const std::int64_t q = 1 + static_cast<std::int64_t>(rng() % book[price]);
                side.cancel(price, q);
                book[price] -= q;
            } else {
                const std::int64_t q = 1 + static_cast<std::int64_t>(rng() % 5);
                side.add(price, q);
                book[price] += q;
            }
        }
        std::set<std::int64_t> live;
        for (auto [pr, q] : book)
            if (q > 0) live.insert(pr);
        const auto b = side.best();
        assert(b.has_value() == !live.empty());
        if (b) assert(*b == (bid ? *live.rbegin() : *live.begin()));
    }

    const std::vector<std::vector<double>> ok = {{1, 0.9, 1.1}, {1 / 0.9, 1, 1.1 / 0.9}, {1 / 1.1, 0.9 / 1.1, 1}};
    assert(!iv::arbitrage_cycle(ok));
    auto bad = ok;
    bad[1][2] = 1.30;
    assert(iv::arbitrage_cycle(bad));
    std::puts("iv_algos_test: all passed");
    return 0;
}
