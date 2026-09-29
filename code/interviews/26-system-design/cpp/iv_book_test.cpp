// The matching core against a brute-force model on seeded random order streams: same fills, same best prices.
#include <cassert>
#include <cstdio>
#include <random>

#include "iv_book.hpp"

struct ModelOrder {
    std::uint64_t id, seq;
    iv::Side side;
    std::int64_t price, qty;
};

// Brute force: scan all resting orders for the best-priced, earliest opposite order, repeatedly.
static std::vector<iv::Fill> model_add(std::vector<ModelOrder>& book, std::uint64_t& seq, std::uint64_t id, iv::Side side,
                                       std::int64_t price, std::int64_t qty) {
    std::vector<iv::Fill> out;
    const bool buy = side == iv::Side::Buy;
    while (qty > 0) {
        int best = -1;
        for (int i = 0; i < static_cast<int>(book.size()); ++i) {
            const auto& o = book[i];
            if (o.side == side) continue;
            if (buy ? o.price > price : o.price < price) continue;
            if (best < 0) {
                best = i;
                continue;
            }
            const auto& b = book[best];
            const bool better = buy ? o.price < b.price : o.price > b.price;
            if (better || (o.price == b.price && o.seq < b.seq)) best = i;
        }
        if (best < 0) break;
        auto& m = book[best];
        const std::int64_t n = std::min(qty, m.qty);
        out.push_back({m.id, id, m.price, n});
        qty -= n;
        m.qty -= n;
        if (m.qty == 0) book.erase(book.begin() + best);
    }
    if (qty > 0) book.push_back({id, seq++, side, price, qty});
    return out;
}

int main() {
    std::mt19937_64 rng(26);
    for (int trial = 0; trial < 200; ++trial) {
        iv::Book book;
        std::vector<ModelOrder> model;
        std::uint64_t seq = 0, next_id = 1;
        std::vector<std::uint64_t> ids;
        for (int step = 0; step < 300; ++step) {
            if (!ids.empty() && rng() % 4 == 0) {
                const auto id = ids[rng() % ids.size()];
                const bool live = std::any_of(model.begin(), model.end(), [&](const ModelOrder& o) { return o.id == id; });
                assert(book.cancel(id) == live);
                std::erase_if(model, [&](const ModelOrder& o) { return o.id == id; });
            } else {
                const auto side = rng() % 2 ? iv::Side::Buy : iv::Side::Sell;
                const std::int64_t price = 95 + static_cast<std::int64_t>(rng() % 11);
                const std::int64_t qty = 1 + static_cast<std::int64_t>(rng() % 9);
                const auto id = next_id++;
                ids.push_back(id);
                assert(book.add(id, side, price, qty) == model_add(model, seq, id, side, price, qty));
            }
            std::optional<std::int64_t> bb, ba;
            for (const auto& o : model) {
                if (o.side == iv::Side::Buy) bb = bb ? std::max(*bb, o.price) : o.price;
                else ba = ba ? std::min(*ba, o.price) : o.price;
            }
            assert(book.best_bid() == bb && book.best_ask() == ba);
            if (bb && ba) assert(*bb < *ba);  // never crossed at rest
        }
    }
    std::puts("iv_book_test: all passed");
    return 0;
}
