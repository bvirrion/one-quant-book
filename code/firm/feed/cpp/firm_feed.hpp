// Feed normaliser (build of Book 1, Chapter 28), C++20. Same wire format as firm_feed.py.
// Header only. No allocation per message on the decode path; the book uses standard containers,
// which a production book would replace (One Quant Book 12).
#pragma once
#include <cstddef>
#include <cstdint>
#include <functional>
#include <map>
#include <span>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

namespace firm::feed {

inline std::uint64_t be(std::span<const std::uint8_t> b, std::size_t off, std::size_t n) {
    std::uint64_t v = 0;
    for (std::size_t i = 0; i < n; ++i) v = (v << 8) | b[off + i];
    return v;
}

struct Msg {
    char kind{};
    std::uint16_t locate{};
    std::uint64_t ts{};       // nanoseconds since midnight
    std::uint64_t ref{};
    char side{};
    std::uint32_t shares{};
    std::uint32_t price{};    // 1/10,000 dollar
    std::uint64_t match{};
};

inline std::size_t expected_length(char kind) {
    switch (kind) {
        case 'A': return 36;
        case 'E': return 31;
        case 'X': return 23;
        case 'D': return 19;
        case 'P': return 44;
        default: return 0;
    }
}

// Calls `on(msg)` for each framed message. Throws on truncation or on a length that does not
// match the type.
inline void decode(std::span<const std::uint8_t> buf, const std::function<void(const Msg&)>& on) {
    std::size_t i = 0;
    while (i < buf.size()) {
        if (i + 2 > buf.size()) throw std::runtime_error("truncated length prefix");
        const std::size_t n = static_cast<std::size_t>(be(buf, i, 2));
        if (i + 2 + n > buf.size()) throw std::runtime_error("truncated message");
        const auto body = buf.subspan(i + 2, n);
        Msg m;
        m.kind = static_cast<char>(body[0]);
        if (expected_length(m.kind) != n) throw std::runtime_error("length does not match type");
        m.locate = static_cast<std::uint16_t>(be(body, 1, 2));
        m.ts = be(body, 5, 6);
        m.ref = be(body, 11, 8);
        switch (m.kind) {
            case 'A':
                m.side = static_cast<char>(body[19]);
                m.shares = static_cast<std::uint32_t>(be(body, 20, 4));
                m.price = static_cast<std::uint32_t>(be(body, 32, 4));
                break;
            case 'E':
                m.shares = static_cast<std::uint32_t>(be(body, 19, 4));
                m.match = be(body, 23, 8);
                break;
            case 'X':
                m.shares = static_cast<std::uint32_t>(be(body, 19, 4));
                break;
            case 'D':
                break;
            case 'P':
                m.side = static_cast<char>(body[19]);
                m.shares = static_cast<std::uint32_t>(be(body, 20, 4));
                m.price = static_cast<std::uint32_t>(be(body, 32, 4));
                m.match = be(body, 36, 8);
                break;
        }
        on(m);
        i += 2 + n;
    }
}

struct Order {
    char side;
    std::uint32_t shares;
    std::uint32_t price;
    std::uint16_t locate;
};

struct Summary {
    std::int64_t best_bid{-1};
    std::uint64_t bid_size{};
    std::int64_t best_ask{-1};
    std::uint64_t ask_size{};
    std::uint64_t trades{};
    std::uint64_t shares_traded{};
    std::uint64_t live_orders{};
    bool operator==(const Summary&) const = default;
};

class Book {
public:
    void apply(const Msg& m) {
        if (m.ts < last_ts_) ++errors_;
        if (m.ts > last_ts_) last_ts_ = m.ts;
        switch (m.kind) {
            case 'A': {
                if (!orders_.emplace(m.ref, Order{m.side, m.shares, m.price, m.locate}).second) { ++errors_; return; }
                level(m.locate, m.side)[m.price] += m.shares;
                break;
            }
            case 'E':
                if (reduce(m.ref, m.shares)) { ++trades_[m.locate]; traded_[m.locate] += m.shares; }
                break;
            case 'X': reduce(m.ref, m.shares); break;
            case 'D': {
                const auto it = orders_.find(m.ref);
                reduce(m.ref, it == orders_.end() ? 0 : it->second.shares);
                break;
            }
            case 'P': ++trades_[m.locate]; traded_[m.locate] += m.shares; break;
            default: ++errors_;
        }
    }

    [[nodiscard]] Summary summary(std::uint16_t locate) const {
        Summary s;
        if (const auto b = levels_.find({locate, 'B'}); b != levels_.end() && !b->second.empty()) {
            s.best_bid = b->second.rbegin()->first;
            s.bid_size = b->second.rbegin()->second;
        }
        if (const auto a = levels_.find({locate, 'S'}); a != levels_.end() && !a->second.empty()) {
            s.best_ask = a->second.begin()->first;
            s.ask_size = a->second.begin()->second;
        }
        if (const auto t = trades_.find(locate); t != trades_.end()) s.trades = t->second;
        if (const auto v = traded_.find(locate); v != traded_.end()) s.shares_traded = v->second;
        for (const auto& [ref, o] : orders_) if (o.locate == locate) ++s.live_orders;
        return s;
    }

    [[nodiscard]] std::uint64_t errors() const { return errors_; }

private:
    using Levels = std::map<std::uint32_t, std::uint64_t>;
    Levels& level(std::uint16_t locate, char side) { return levels_[{locate, side}]; }

    bool reduce(std::uint64_t ref, std::uint32_t shares) {
        const auto it = orders_.find(ref);
        if (it == orders_.end()) { ++errors_; return false; }
        Order& o = it->second;
        if (shares > o.shares) { ++errors_; shares = o.shares; }
        auto& lv = level(o.locate, o.side);
        auto p = lv.find(o.price);
        p->second -= shares;
        if (p->second == 0) lv.erase(p);
        o.shares -= shares;
        if (o.shares == 0) orders_.erase(it);
        return true;
    }

    std::unordered_map<std::uint64_t, Order> orders_;
    std::map<std::pair<std::uint16_t, char>, Levels> levels_;
    std::map<std::uint16_t, std::uint64_t> trades_, traded_;
    std::uint64_t last_ts_{0}, errors_{0};
};

}  // namespace firm::feed
