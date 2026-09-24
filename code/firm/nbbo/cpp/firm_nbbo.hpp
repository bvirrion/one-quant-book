#pragma once
// firm.nbbo -- consolidated best bid and offer (build of Chapter 9, One Quant Book 1), C++20.
// Fixed venue table, no allocation: update() is O(number of venues).
#include <array>
#include <cstdint>
#include <optional>
#include <stdexcept>

namespace firm {

inline constexpr std::size_t kMaxVenues = 32;

struct Quote {
    std::int64_t bid = 0, bid_size = 0, ask = 0, ask_size = 0;
    bool live = false;
};

struct Nbbo {
    std::int64_t bid, bid_size, ask, ask_size;
    std::uint32_t bid_venues, ask_venues;  // bit masks over venue ids
    bool locked() const { return bid == ask; }
    bool crossed() const { return bid > ask; }
    bool operator==(const Nbbo&) const = default;
};

class NbboBuilder {
public:
    explicit NbboBuilder(std::int64_t round_lot = 100) : round_lot_(round_lot) {}

    // Returns the new NBBO if it changed.
    std::optional<Nbbo> update(std::size_t venue, std::int64_t bid, std::int64_t bid_size,
                               std::int64_t ask, std::int64_t ask_size) {
        if (venue >= kMaxVenues || bid <= 0 || ask <= 0 || bid_size < 0 || ask_size < 0)
            throw std::invalid_argument("bad quote");
        const auto before = nbbo();
        quotes_[venue] = Quote{bid, bid_size, ask, ask_size, true};
        const auto after = nbbo();
        return after == before ? std::nullopt : after;
    }

    std::optional<Nbbo> nbbo() const {
        Nbbo n{0, 0, 0, 0, 0, 0};
        bool has_bid = false, has_ask = false;
        for (std::size_t v = 0; v < kMaxVenues; ++v) {
            const Quote& q = quotes_[v];
            if (!q.live) continue;
            if (q.bid_size >= round_lot_) {
                if (!has_bid || q.bid > n.bid) { n.bid = q.bid; n.bid_size = 0; n.bid_venues = 0; has_bid = true; }
                if (q.bid == n.bid) { n.bid_size += q.bid_size; n.bid_venues |= 1u << v; }
            }
            if (q.ask_size >= round_lot_) {
                if (!has_ask || q.ask < n.ask) { n.ask = q.ask; n.ask_size = 0; n.ask_venues = 0; has_ask = true; }
                if (q.ask == n.ask) { n.ask_size += q.ask_size; n.ask_venues |= 1u << v; }
            }
        }
        if (!has_bid || !has_ask) return std::nullopt;
        return n;
    }

    bool trades_through(int side, std::int64_t price) const {
        const auto n = nbbo();
        if (!n) return false;
        return side > 0 ? price > n->ask : price < n->bid;
    }

private:
    std::int64_t round_lot_;
    std::array<Quote, kMaxVenues> quotes_{};
};

}  // namespace firm
