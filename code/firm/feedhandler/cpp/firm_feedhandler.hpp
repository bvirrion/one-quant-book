// firm.feedhandler -- the market-data feed handler in C++20 (build of One Quant Book 13, chapter 18): the Python
// reference's algorithm, event for event and hash for hash. Arbitration by packet sequence number, gap detection with
// a timeout for the other line, retransmission, snapshot recovery, normalisation to the firm's 48-byte event record,
// a stale-book flag and counters. In the steady state (no gap) nothing is allocated per packet.
#pragma once
#include <cstdint>
#include <cstring>
#include <functional>
#include <map>
#include <queue>
#include <vector>

#include "../../wirecodec/cpp/firm_wirecodec.hpp"

namespace firm::feed2 {

using firm::wire::be;
using firm::wire::be16;
using firm::wire::be32;
using firm::wire::be64;

struct Packet {
    std::uint64_t t;
    const std::uint8_t* p;
    std::uint32_t n;
};

inline std::vector<Packet> recorded(const std::vector<std::uint8_t>& f) {
    std::vector<Packet> out;
    for (std::size_t i = 0; i + 12 <= f.size();) {
        const auto n = be32(f.data() + i + 8);
        out.push_back({be64(f.data() + i), f.data() + i + 12, n});
        i += 12 + n;
    }
    return out;
}

// The firm's normalised event: 48 bytes when packed little-endian (kind, side, locate, seq, ts, ref, ref2, price, qty).
struct Event {
    std::uint8_t kind = 0, side = 0;
    std::uint16_t locate = 0;
    std::uint64_t seq = 0, ts = 0, ref = 0, ref2 = 0;
    std::uint32_t price = 0;
    std::uint64_t qty = 0;
};

inline Event normalise(const std::uint8_t* m, std::uint64_t seq) {
    Event e;
    e.kind = m[0];
    e.locate = be16(m + 1);
    e.ts = be(m + 5, 6);
    e.seq = seq;
    switch (m[0]) {
        case 'A': e.ref = be64(m + 11); e.side = m[19]; e.qty = be32(m + 20); e.price = be32(m + 32); break;
        case 'E': e.ref = be64(m + 11); e.qty = be32(m + 19); e.ref2 = be64(m + 23); break;
        case 'X': e.ref = be64(m + 11); e.qty = be32(m + 19); break;
        case 'D': e.ref = be64(m + 11); break;
        case 'P': e.side = m[19]; e.qty = be32(m + 20); e.price = be32(m + 32); e.ref2 = be64(m + 36); break;
        case 'U': e.ref = be64(m + 11); e.ref2 = be64(m + 19); e.qty = be32(m + 27); e.price = be32(m + 31); break;
        case 'C': e.ref = be64(m + 11); e.qty = be32(m + 19); e.ref2 = be64(m + 23); e.price = be32(m + 32); break;
        case 'Q': e.qty = be64(m + 11); e.price = be32(m + 27); e.ref2 = be64(m + 31); break;
        case 'G': case 'W': e.ref2 = be64(m + 11); break;
        default: break;
    }
    return e;
}

inline std::uint64_t fnv1a(const Event& e, std::uint64_t h) {
    std::uint8_t b[48];
    b[0] = e.kind;
    b[1] = e.side;
    std::memcpy(b + 2, &e.locate, 2);
    std::memcpy(b + 4, &e.seq, 8);
    std::memcpy(b + 12, &e.ts, 8);
    std::memcpy(b + 20, &e.ref, 8);
    std::memcpy(b + 28, &e.ref2, 8);
    std::memcpy(b + 36, &e.price, 4);
    std::memcpy(b + 40, &e.qty, 8);
    for (const auto c : b) h = (h ^ c) * 0x100000001B3ULL;
    return h;
}

// Calls f(sequence number, message) for each message of a MoldUDP64 packet; returns (first seq, count).
template <class F>
inline std::pair<std::uint64_t, std::uint64_t> blocks(const std::uint8_t* p, F&& f) {
    const std::uint64_t seq = be64(p + 10);
    const std::uint16_t c = be16(p + 18);
    if (c == 0 || c == 0xFFFF) return {seq, 0};
    std::size_t i = 20;
    for (std::uint16_t k = 0; k < c; ++k) {
        const std::size_t n = be16(p + i);
        f(seq + k, p + i + 2);
        i += 2 + n;
    }
    return {seq, c};
}

// The simulator's retransmission service: messages seq .. seq+count-1 from the last `window` published.
class RetxServer {
public:
    RetxServer(std::vector<Packet> clean, std::uint64_t window, std::uint64_t max_count = 1000)
        : clean_(std::move(clean)), window_(window), max_(max_count) {}
    // Packets answering the request, or false if the server cannot (older than its window).
    bool request(std::uint64_t t, std::uint64_t seq, std::uint64_t count, std::vector<Packet>& out) const {
        std::uint64_t published = 0;
        for (const auto& k : clean_) {
            if (k.t > t) break;
            const auto [s, c] = blocks(k.p, [](std::uint64_t, const std::uint8_t*) {});
            if (s + c - 1 > published && c > 0) published = s + c - 1;
        }
        if (seq + window_ <= published || count == 0) return false;
        if (count > max_) count = max_;
        for (const auto& k : clean_) {
            if (k.t > t) break;
            const auto [s, c] = blocks(k.p, [](std::uint64_t, const std::uint8_t*) {});
            if (s < seq + count && s + c > seq) out.push_back(k);
        }
        return true;
    }

private:
    std::vector<Packet> clean_;
    std::uint64_t window_, max_;
};

struct Counters {
    std::uint64_t packets = 0, messages = 0, duplicates = 0, gaps = 0, filled_by_line = 0, retransmissions = 0,
                  snapshots = 0;
};

class Handler {
public:
    enum class Mode { live, await_line, await_retx, await_snapshot };

    explicit Handler(const RetxServer* retx = nullptr, std::uint64_t gap_timeout_ns = 500'000,
                     std::uint64_t rtt_ns = 200'000)
        : retx_(retx), timeout_(gap_timeout_ns), rtt_(rtt_ns) {}

    // on_event is called for every published event (the firm's ring in production, a vector in tests).
    std::function<void(const Event&)> on_event;
    std::uint64_t hash = 0xCBF29CE484222325ULL, events = 0;
    std::vector<std::pair<std::uint64_t, std::uint64_t>> stale;
    Counters c;
    Mode mode = Mode::live;
    // Optional instrumentation for benchmarks: a clock read around the handling of each input.
    std::uint64_t (*clock)() = nullptr;
    std::vector<std::uint32_t>* timings = nullptr;

    // src: 'A', 'B', 'S' (snapshot); packets must outlive the run.
    void run(const std::vector<Packet>& a, const std::vector<Packet>& b, const std::vector<Packet>& s) {
        std::uint64_t n = 0;
        // merge exactly as the reference does: by time, then A before B before S, stable
        std::size_t i = 0, j = 0, k = 0;
        while (i < a.size() || j < b.size() || k < s.size()) {
            const std::uint64_t ta = i < a.size() ? a[i].t : UINT64_MAX, tb = j < b.size() ? b[j].t : UINT64_MAX,
                                ts = k < s.size() ? s[k].t : UINT64_MAX;
            if (ta <= tb && ta <= ts) q_.push({a[i].t, 0, n++, 0, 'A', a[i++]});
            else if (tb <= ts) q_.push({b[j].t, 0, n++, 0, 'B', b[j++]});
            else q_.push({s[k].t, 1, n++, 0, 'S', s[k++]});
        }
        while (!q_.empty()) {
            const Item it = q_.top();
            q_.pop();
            const std::uint64_t t0 = clock ? clock() : 0;
            on_packet(it.t, it.src, it.pk.p);
            if (clock && timings) timings->push_back(static_cast<std::uint32_t>(clock() - t0));
        }
    }

    // One input as it arrives (live use, chapter 26): src 'A' or 'B' (an incremental packet), 'S' (a snapshot) or
    // 'D' (a retransmission deadline); t is the arrival time on the recording's clock.
    void on_packet(std::uint64_t t, char src, const std::uint8_t* p) {
        if (mode == Mode::await_line && t >= deadline_) timeout(deadline_);
        if (src == 'S') snapshot(t, p);
        else if (src == 'D') {
            if (mode == Mode::await_retx && !pending_.empty()) timeout(t);
        } else incremental(t, p);
    }

private:
    struct Item {
        std::uint64_t t, pri, n, sub;
        char src;
        Packet pk;
        bool operator>(const Item& o) const {
            if (t != o.t) return t > o.t;
            if (pri != o.pri) return pri > o.pri;
            if (n != o.n) return n > o.n;
            return sub > o.sub;
        }
    };

    void publish(const Event& e) {
        hash = fnv1a(e, hash);
        ++events;
        if (on_event) on_event(e);
    }

    void drain(std::uint64_t t) {
        for (auto it = pending_.find(next_); it != pending_.end(); it = pending_.find(next_)) {
            publish(normalise(it->second, next_));
            ++c.messages;
            pending_.erase(it);
            ++next_;
        }
        if (mode != Mode::live && pending_.empty()) {
            if (mode == Mode::await_line) ++c.filled_by_line;
            stale.emplace_back(since_, t);
            mode = Mode::live;
        }
    }

    void incremental(std::uint64_t t, const std::uint8_t* p) {
        ++c.packets;
        const std::uint64_t seq = be64(p + 10), cnt = be16(p + 18);
        if (cnt != 0 && cnt != 0xFFFF && seq + cnt <= next_) {
            ++c.duplicates;
            return;
        }
        blocks(p, [&](std::uint64_t s, const std::uint8_t* m) {
            if (s < next_) return;
            if (s == next_ && mode == Mode::live) {
                publish(normalise(m, s));
                ++c.messages;
                ++next_;
            } else {
                pending_.emplace(s, m);
            }
        });
        if (!pending_.empty() && mode == Mode::live) {
            mode = Mode::await_line;
            since_ = t;
            deadline_ = t + timeout_;
            ++c.gaps;
        }
        drain(t);
    }

    void timeout(std::uint64_t t) {
        const std::uint64_t first_held = pending_.begin()->first;
        std::vector<Packet> reply;
        const bool ok = retx_ && retx_->request(t, next_, first_held - next_, reply);
        if (!ok) {
            ++c.snapshots;
            mode = Mode::await_snapshot;
            return;
        }
        ++c.retransmissions;
        mode = Mode::await_retx;
        std::uint64_t sub = 0;
        for (const auto& k : reply) q_.push({t + rtt_, 2, events, sub++, 'R', k});
        q_.push({t + rtt_, 2, events, sub, 'D', Packet{0, nullptr, 0}});   // after the answer: ask for the rest
    }

    void snapshot(std::uint64_t t, const std::uint8_t* p) {
        if (mode != Mode::await_snapshot) return;
        blocks(p, [&](std::uint64_t, const std::uint8_t* m) {
            if (m[0] == 'G') {
                snap_.assign(1, m);
            } else if (!snap_.empty()) {
                snap_.push_back(m);
                if (m[0] == 'W') apply_snapshot(t);
            }
        });
    }

    void apply_snapshot(std::uint64_t t) {
        const std::uint64_t upto = be64(snap_[0] + 11);
        if (upto + 1 < next_) {
            snap_.clear();
            return;
        }
        for (const auto* m : snap_) publish(normalise(m, upto));
        snap_.clear();
        next_ = upto + 1;
        pending_.erase(pending_.begin(), pending_.upper_bound(upto));
        drain(t);
        if (!pending_.empty() && mode != Mode::live) {
            mode = Mode::await_line;
            deadline_ = t + timeout_;
        }
    }

    const RetxServer* retx_;
    std::uint64_t timeout_, rtt_;
    std::uint64_t next_ = 1, since_ = 0, deadline_ = 0;
    std::map<std::uint64_t, const std::uint8_t*> pending_;
    std::vector<const std::uint8_t*> snap_;
    std::priority_queue<Item, std::vector<Item>, std::greater<Item>> q_;
};

}  // namespace firm::feed2
