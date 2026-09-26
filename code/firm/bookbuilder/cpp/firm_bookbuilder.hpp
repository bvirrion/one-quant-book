// firm.bookbuilder -- the order-by-order book builder in C++20 (build of One Quant Book 13, chapter 19).
// Orders live in a fixed pool found through an open-addressing hash map; price levels live in a dense ladder of W ticks
// around the touch, recentred when the touch leaves its middle half, with a sparse map for the rare order far outside
// it. Level 2 after every event equals the Python reference's (a hash of the top five levels a side). After
// construction, applying events allocates nothing unless an order lands outside the ladder.
#pragma once
#include <cstdint>
#include <cstring>
#include <map>
#include <string>
#include <vector>

#include "../../feedhandler/cpp/firm_feedhandler.hpp"

namespace firm::book {

using firm::feed2::Event;

// ref -> slot. Linear probing in a power-of-two table; deletion shifts the following entries back instead of leaving
// tombstones, so that lookups never slow down as orders come and go.
class OrderMap {
public:
    explicit OrderMap(std::size_t capacity_pow2) : keys_(capacity_pow2, 0), vals_(capacity_pow2, 0), mask_(capacity_pow2 - 1) {}

    std::uint32_t* find(std::uint64_t ref) {
        for (std::size_t i = slot(ref);; i = (i + 1) & mask_) {
            if (keys_[i] == ref) return &vals_[i];
            if (keys_[i] == 0) return nullptr;
        }
    }
    void insert(std::uint64_t ref, std::uint32_t v) {   // ref != 0; the table is never full (capacity >= 2 x orders)
        std::size_t i = slot(ref);
        while (keys_[i] != 0 && keys_[i] != ref) i = (i + 1) & mask_;
        keys_[i] = ref;
        vals_[i] = v;
    }
    void erase(std::uint64_t ref) {
        std::size_t i = slot(ref);
        while (keys_[i] != ref) {
            if (keys_[i] == 0) return;
            i = (i + 1) & mask_;
        }
        // backward shift: move later entries of the probe run into the hole when their home slot allows it
        for (std::size_t j = (i + 1) & mask_; keys_[j] != 0; j = (j + 1) & mask_) {
            const std::size_t home = slot(keys_[j]);
            if (((j - home) & mask_) >= ((j - i) & mask_)) {
                keys_[i] = keys_[j];
                vals_[i] = vals_[j];
                i = j;
            }
        }
        keys_[i] = 0;
    }

private:
    std::size_t slot(std::uint64_t ref) const { return static_cast<std::size_t>((ref * 0x9E3779B97F4A7C15ULL) >> 20) & mask_; }
    std::vector<std::uint64_t> keys_;
    std::vector<std::uint32_t> vals_;
    std::size_t mask_;
};

struct Level {
    std::uint64_t qty = 0;
    std::uint32_t orders = 0;
};

class LadderBook {
public:
    static constexpr std::uint8_t kBid = 'B', kAsk = 'S';

    // tick: the instrument's tick in price units; width: ladder size in ticks (a power of two); max_orders: pool size
    LadderBook(std::uint32_t tick, std::size_t width = 4096, std::size_t max_orders = 1 << 16)
        : tick_(tick), w_(static_cast<std::int64_t>(width)), bids_(width), asks_(width), ba_(w_), map_(4 * max_orders) {
        pool_.resize(max_orders);
        free_.reserve(max_orders);
        for (std::size_t i = max_orders; i-- > 0;) free_.push_back(static_cast<std::uint32_t>(i));
    }

    bool stale = false;
    std::uint64_t recentrings = 0;

    void apply(const Event& e) {
        switch (e.kind) {
            case 'A': add(e.ref, e.side, e.price, e.qty); break;
            case 'E': case 'X': case 'C': reduce(e.ref, e.qty); break;
            case 'D': {
                if (const auto* s = map_.find(e.ref)) reduce(e.ref, pool_[*s].qty);
                break;
            }
            case 'U': {
                if (const auto* s = map_.find(e.ref)) {
                    const std::uint8_t side = pool_[*s].side;
                    reduce(e.ref, pool_[*s].qty);
                    add(e.ref2, side, e.price, e.qty);
                }
                break;
            }
            case 'G': reset(); stale = true; break;
            case 'W': stale = false; break;
            default: break;
        }
    }

    // Best price and quantity of a side; false if the side is empty.
    bool best(std::uint8_t side, std::uint32_t& price, std::uint64_t& qty) const {
        if (side == kBid) {
            if (bb_ >= 0) { price = price_of(bb_); qty = bids_[static_cast<std::size_t>(bb_)].qty; return true; }
            if (!far_bids_.empty()) { price = far_bids_.rbegin()->first; qty = far_bids_.rbegin()->second.qty; return true; }
        } else {
            if (ba_ < w_) { price = price_of(ba_); qty = asks_[static_cast<std::size_t>(ba_)].qty; return true; }
            if (!far_asks_.empty()) { price = far_asks_.begin()->first; qty = far_asks_.begin()->second.qty; return true; }
        }
        return false;
    }

    // Up to n levels of a side, best first: ladder levels, then the far map's.
    std::size_t depth(std::uint8_t side, std::size_t n, std::uint32_t* prices, std::uint64_t* qtys) const {
        std::size_t k = 0;
        if (side == kBid) {
            for (std::int64_t i = bb_; i >= 0 && k < n; --i)
                if (bids_[static_cast<std::size_t>(i)].qty) { prices[k] = price_of(i); qtys[k++] = bids_[static_cast<std::size_t>(i)].qty; }
            for (auto it = far_bids_.rbegin(); it != far_bids_.rend() && k < n; ++it) { prices[k] = it->first; qtys[k++] = it->second.qty; }
        } else {
            for (std::int64_t i = ba_; i < w_ && k < n; ++i)
                if (asks_[static_cast<std::size_t>(i)].qty) { prices[k] = price_of(i); qtys[k++] = asks_[static_cast<std::size_t>(i)].qty; }
            for (auto it = far_asks_.begin(); it != far_asks_.end() && k < n; ++it) { prices[k] = it->first; qtys[k++] = it->second.qty; }
        }
        return k;
    }

    // Invariants (the debug build calls this after every event): levels equal the sum of their orders, no empty level
    // is marked best, the book is not crossed. Returns an empty string when they hold.
    std::string check() const {
        std::vector<Level> b(static_cast<std::size_t>(w_)), a(static_cast<std::size_t>(w_));
        for (const auto& o : pool_) {
            if (!o.live) continue;
            const std::int64_t i = index_of(o.price);
            if (i < 0 || i >= w_) continue;
            auto& lv = (o.side == kBid ? b : a)[static_cast<std::size_t>(i)];
            lv.qty += o.qty;
            ++lv.orders;
        }
        for (std::int64_t i = 0; i < w_; ++i) {
            const auto k = static_cast<std::size_t>(i);
            if (b[k].qty != bids_[k].qty || a[k].qty != asks_[k].qty) return "level sums differ from orders";
        }
        std::uint32_t pb, pa;
        std::uint64_t q;
        if (best(kBid, pb, q) && best(kAsk, pa, q) && pb >= pa) return "crossed";
        return "";
    }

private:
    struct Order {
        std::uint32_t price = 0, qty = 0;
        std::uint8_t side = 0;
        bool live = false;
    };

    std::uint32_t price_of(std::int64_t i) const { return static_cast<std::uint32_t>(base_ + i * tick_); }
    std::int64_t index_of(std::uint32_t price) const { return (static_cast<std::int64_t>(price) - base_) / tick_; }

    // Change a level by dq (negative to reduce) and by count orders, keeping the best indices right.
    void level_add(std::uint8_t side, std::uint32_t price, std::int64_t dq, int count) {
        const std::int64_t i = index_of(price);
        if (i >= 0 && i < w_) {
            auto& lv = (side == kBid ? bids_ : asks_)[static_cast<std::size_t>(i)];
            lv.qty = static_cast<std::uint64_t>(static_cast<std::int64_t>(lv.qty) + dq);
            lv.orders = static_cast<std::uint32_t>(static_cast<int>(lv.orders) + count);
            if (side == kBid && lv.qty && i > bb_) bb_ = i;
            if (side == kAsk && lv.qty && i < ba_) ba_ = i;
            if (side == kBid && i == bb_ && !lv.qty) while (bb_ >= 0 && !bids_[static_cast<std::size_t>(bb_)].qty) --bb_;
            if (side == kAsk && i == ba_ && !lv.qty) while (ba_ < w_ && !asks_[static_cast<std::size_t>(ba_)].qty) ++ba_;
            return;
        }
        auto& far = side == kBid ? far_bids_ : far_asks_;   // outside the ladder: the sparse fallback (allocates)
        auto& lv = far[price];
        lv.qty = static_cast<std::uint64_t>(static_cast<std::int64_t>(lv.qty) + dq);
        lv.orders = static_cast<std::uint32_t>(static_cast<int>(lv.orders) + count);
        if (!lv.qty) far.erase(price);
    }

    void add(std::uint64_t ref, std::uint8_t side, std::uint32_t price, std::uint64_t qty) {
        if (free_.empty() || map_.find(ref)) return;
        if (!centred_) centre(price);
        const std::int64_t i = index_of(price);
        if ((side == kBid && i >= w_) || (side == kAsk && i < 0)) {   // a new best beyond the ladder: move it first
            centre(price);
            ++recentrings;
        }
        const std::uint32_t s = free_.back();
        free_.pop_back();
        pool_[s] = Order{price, static_cast<std::uint32_t>(qty), side, true};
        ++live_;
        map_.insert(ref, s);
        level_add(side, price, static_cast<std::int64_t>(qty), 1);
        maybe_recentre();
    }

    void reduce(std::uint64_t ref, std::uint64_t qty) {
        std::uint32_t* s = map_.find(ref);
        if (!s) return;
        Order& o = pool_[*s];
        if (qty > o.qty) qty = o.qty;
        o.qty -= static_cast<std::uint32_t>(qty);
        level_add(o.side, o.price, -static_cast<std::int64_t>(qty), 0);
        if (o.qty == 0) {
            if (const std::int64_t i = index_of(o.price); i >= 0 && i < w_) {
                auto& lv = (o.side == kBid ? bids_ : asks_)[static_cast<std::size_t>(i)];
                --lv.orders;
            }
            o.live = false;
            --live_;
            free_.push_back(*s);
            map_.erase(ref);
        }
        maybe_recentre();
    }

    // The ladder follows the touch: when a best price leaves the middle half, move the base so that the mid is at the
    // centre, and re-file every live order (the only full pass, and no allocation unless orders fall outside).
    void maybe_recentre() {
        const bool bid = bb_ >= 0, ask = ba_ < w_;
        if ((!bid || (bb_ >= w_ / 4 && bb_ < 3 * w_ / 4)) && (!ask || (ba_ >= w_ / 4 && ba_ < 3 * w_ / 4))) return;
        const std::int64_t mid = bid && ask ? (price_of(bb_) + price_of(ba_)) / 2 : price_of(bid ? bb_ : ba_);
        centre(static_cast<std::uint32_t>(mid));
        ++recentrings;
    }

    void centre(std::uint32_t mid) {
        base_ = static_cast<std::int64_t>(mid) - (w_ / 2) * tick_;
        base_ -= base_ % tick_;
        centred_ = true;
        std::fill(bids_.begin(), bids_.end(), Level{});
        std::fill(asks_.begin(), asks_.end(), Level{});
        far_bids_.clear();
        far_asks_.clear();
        bb_ = -1;
        ba_ = w_;
        if (live_ == 0) return;
        for (const auto& o : pool_)
            if (o.live) level_add(o.side, o.price, o.qty, 1);   // o.qty converts to a positive change
    }

    void reset() {
        for (auto& o : pool_) o.live = false;
        live_ = 0;
        free_.clear();
        for (std::size_t i = pool_.size(); i-- > 0;) free_.push_back(static_cast<std::uint32_t>(i));
        map_ = OrderMap(4 * pool_.size());
        centred_ = false;
        std::fill(bids_.begin(), bids_.end(), Level{});
        std::fill(asks_.begin(), asks_.end(), Level{});
        far_bids_.clear();
        far_asks_.clear();
        bb_ = -1;
        ba_ = w_;
    }

    std::int64_t tick_, w_, base_ = 0;
    std::size_t live_ = 0;
    bool centred_ = false;
    std::vector<Level> bids_, asks_;
    std::int64_t bb_ = -1, ba_;
    std::map<std::uint32_t, Level> far_bids_, far_asks_;
    std::vector<Order> pool_;
    std::vector<std::uint32_t> free_;
    OrderMap map_;
};

// FNV-1a of the top n levels of both sides (price u32, qty u64, little-endian), empty levels as zeros.
template <class Book>
std::uint64_t l2_hash(const Book& b, std::uint64_t h, std::size_t n = 5) {
    std::uint32_t p[16];
    std::uint64_t q[16];
    for (const std::uint8_t side : {LadderBook::kBid, LadderBook::kAsk}) {
        const std::size_t k = b.depth(side, n, p, q);
        for (std::size_t i = 0; i < n; ++i) {
            std::uint8_t rec[12];
            const std::uint32_t pp = i < k ? p[i] : 0;
            const std::uint64_t qq = i < k ? q[i] : 0;
            std::memcpy(rec, &pp, 4);
            std::memcpy(rec + 4, &qq, 8);
            for (const auto c : rec) h = (h ^ c) * 0x100000001B3ULL;
        }
    }
    return h;
}

}  // namespace firm::book
