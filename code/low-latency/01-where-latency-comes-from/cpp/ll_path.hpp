// A toy tick-to-trade path (One Quant Book 13, chapter 1): decode one framed message, apply it to
// Book 1's book, decide, and encode an order. Each stage is a function so it can be timed alone.
#pragma once
#include <array>
#include <cstdint>
#include <span>

#include "../../../firm/feed/cpp/firm_feed.hpp"

namespace ll::path {

using firm::feed::Msg;

// Stage 1: decode exactly one length-prefixed message.
inline Msg decode_one(std::span<const std::uint8_t> frame) {
    Msg out{};
    firm::feed::decode(frame, [&](const Msg& m) { out = m; });
    return out;
}

// Stage 3: a toy decision. Keep an exponentially weighted price of recent adds on each side and
// send a buy when an ask is added within `edge` (in 1/10,000 dollar) of the bid-side average.
struct Decider {
    double bid_avg = 0.0, ask_avg = 0.0, edge = 700.0;
    std::uint64_t sent = 0;
    bool on(const Msg& m) {
        if (m.kind != 'A') return false;
        const double p = static_cast<double>(m.price);
        double& avg = m.side == 'B' ? bid_avg : ask_avg;
        avg = avg == 0.0 ? p : 0.9 * avg + 0.1 * p;
        const bool go = m.side == 'S' && bid_avg > 0.0 && p - bid_avg <= edge;
        sent += go;
        return go;
    }
};

// Stage 4: encode a 47-byte enter-order message in the style of an OUCH-like protocol, big-endian.
inline void put_be(std::uint8_t* p, std::uint64_t v, int n) {
    for (int i = n - 1; i >= 0; --i) { p[i] = static_cast<std::uint8_t>(v); v >>= 8; }
}

inline std::size_t encode_order(std::array<std::uint8_t, 64>& buf, std::uint64_t token, char side,
                                std::uint32_t qty, std::uint16_t locate, std::uint32_t price) {
    buf[0] = 'O';
    put_be(&buf[1], token, 8);
    buf[9] = static_cast<std::uint8_t>(side);
    put_be(&buf[10], qty, 4);
    put_be(&buf[14], locate, 2);
    put_be(&buf[16], price, 4);
    buf[20] = 'D';  // time in force: day
    for (int i = 21; i < 47; ++i) buf[static_cast<std::size_t>(i)] = 0;
    return 47;
}

}  // namespace ll::path
