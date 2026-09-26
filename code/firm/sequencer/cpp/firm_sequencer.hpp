// firm.sequencer (C++20): the journal with fencing epochs and the replicated trading state machine, twin of the Python
// reference (firm_sequencer.py). Every replica applies the journal in sequence order and reaches the same state, hash
// included; an append under an epoch older than the journal's is refused, so that a primary that has been replaced
// cannot write any more. Same journal, same states as data/expected.txt.
#pragma once
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <initializer_list>
#include <map>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace firm::seq {

inline constexpr std::int64_t kLimit = 1'000, kSize = 100, kAggress = 300;
inline constexpr std::size_t kMaxOpen = 3;

// kind: 'M' price | 'E' cl qty leaves | 'C' cl | 'J' cl reason | 'Q' cl | 'A' key_seq key_idx new_cl
struct Entry {
    std::int64_t epoch = 0, seq = 0;
    char kind = 0;
    std::int64_t a = 0, b = 0, c = 0;
    char reason = 0;
};

class Journal {
public:
    // The sequence number of the new entry; throws if the writer's epoch has been fenced off.
    std::int64_t append(Entry e) {
        if (e.epoch < epoch_) throw std::runtime_error("fenced: an older epoch cannot append");
        e.seq = static_cast<std::int64_t>(entries_.size()) + 1;
        entries_.push_back(e);
        return e.seq;
    }
    void fence(std::int64_t epoch) {
        if (epoch <= epoch_) throw std::runtime_error("a new epoch must be larger");
        epoch_ = epoch;
    }
    std::int64_t epoch() const { return epoch_; }
    const std::vector<Entry>& entries() const { return entries_; }

private:
    std::vector<Entry> entries_;
    std::int64_t epoch_ = 1;
};

struct Order {
    std::int64_t key_seq, key_idx;
    char side;
    std::int64_t qty, price, filled = 0;
};

inline std::int64_t cl_for(std::int64_t key_seq, std::int64_t key_idx) { return key_seq * 16 + key_idx; }

class Replica {
public:
    std::int64_t position = 0, last_price = 0, applied = 0, reports_seen = 0;
    std::uint64_t hash = 0xCBF29CE484222325ULL;
    std::map<std::int64_t, Order> open, abandoned;  // by client order identifier

    struct Out {
        std::int64_t cl;
        char side;
        std::int64_t qty, price;
    };

    // Applies the next entry; returns the orders it decides to send (at most one here).
    std::vector<Out> apply(const Entry& e) {
        if (e.seq != applied + 1) throw std::runtime_error("gap in the journal");
        applied = e.seq;
        std::vector<Out> out;
        if (e.kind == 'M') {
            const std::int64_t p = e.a;
            if (last_price && p != last_price && open.size() < kMaxOpen) {
                const char side = p < last_price ? 'B' : 'S';
                const std::int64_t room = kLimit - (side == 'B' ? position : -position) - open_qty(side);
                if (room >= kSize) {
                    const std::int64_t cl = cl_for(e.seq, 0);
                    const std::int64_t price = side == 'B' ? p + kAggress : p - kAggress;
                    open[cl] = Order{e.seq, 0, side, kSize, price};
                    out.push_back({cl, side, kSize, price});
                    mix({e.seq, 0, side, kSize, price});
                }
            }
            last_price = p;
        } else if (e.kind == 'A') {  // resent under a new identifier: the old one is given up for lost
            for (auto it = open.begin(); it != open.end(); ++it)
                if (it->second.key_seq == e.a && it->second.key_idx == e.b) {
                    const Order o = it->second;
                    abandoned[it->first] = o;
                    open.erase(it);
                    open[e.c] = Order{o.key_seq, o.key_idx, o.side, o.qty, o.price};
                    break;
                }
            mix({e.seq, e.c});
        } else {
            ++reports_seen;
            const std::int64_t cl = e.a;
            auto it = open.find(cl);
            if (it == open.end()) {
                auto ab = abandoned.find(cl);
                if (ab != abandoned.end()) {  // a report for an identifier given up: it did reach the venue
                    if (e.kind == 'E') position += ab->second.side == 'B' ? e.b : -e.b;
                    if (e.kind == 'C' || (e.kind == 'E' && e.c == 0)) abandoned.erase(ab);
                }
            } else if (e.kind == 'E') {
                it->second.filled += e.b;
                position += it->second.side == 'B' ? e.b : -e.b;
                if (e.c == 0) open.erase(it);
            } else if (e.kind == 'C' || (e.kind == 'J' && e.reason != 'D')) {
                open.erase(it);
            }
        }
        mix({e.seq, position, static_cast<std::int64_t>(open.size())});
        return out;
    }

    // Open orders no report has mentioned: (key seq, key index), sorted.
    std::vector<std::pair<std::int64_t, std::int64_t>> unacknowledged() const {
        std::vector<std::pair<std::int64_t, std::int64_t>> k;
        for (const auto& [cl, o] : open)
            if (o.filled == 0) k.emplace_back(o.key_seq, o.key_idx);
        std::sort(k.begin(), k.end());
        return k;
    }

private:
    std::int64_t open_qty(char side) const {
        std::int64_t q = 0;
        for (const auto& [cl, o] : open)
            if (o.side == side) q += o.qty - o.filled;
        return q;
    }
    void mix(std::initializer_list<std::int64_t> vals) {
        for (std::int64_t v : vals)
            for (int i = 0; i < 8; ++i)
                hash = (hash ^ static_cast<std::uint8_t>(static_cast<std::uint64_t>(v) >> (8 * i))) * 0x100000001B3ULL;
    }
};

// One line of data/journal.txt.
inline Entry parse(const std::string& line) {
    Entry e;
    char k[4] = {0}, r[4] = {0};
    long long ep, sq, a = 0, b = 0, c = 0;
    std::sscanf(line.c_str(), "%lld %lld %3s", &ep, &sq, k);
    e.epoch = ep, e.seq = sq, e.kind = k[0];
    const char* rest = line.c_str();
    for (int i = 0; i < 3; ++i) rest = std::strchr(rest, ' ') + 1;
    if (e.kind == 'J') std::sscanf(rest, "%lld %3s", &a, r);
    else std::sscanf(rest, "%lld %lld %lld", &a, &b, &c);
    e.a = a, e.b = b, e.c = c, e.reason = r[0];
    return e;
}

}  // namespace firm::seq
