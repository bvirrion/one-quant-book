// firm.exchsim codec (One Quant Book 10, chapter 26), C++20: the byte layouts of PROTOCOL.md / schema.json.
// Big-endian; decode never allocates (it fills a plain struct from a byte span); encode appends to a buffer.
// One struct per protocol carries every field any message of that protocol uses; `type` selects the layout.
#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <span>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace firm::exchsim {

using u8 = std::uint8_t;
using u16 = std::uint16_t;
using u32 = std::uint32_t;
using u64 = std::uint64_t;
using i64 = std::int64_t;
using Bytes = std::vector<u8>;
using Span = std::span<const u8>;

// ---------------------------------------------------------------------------------------------- primitives
inline void put(Bytes& b, u64 v, int n) {
    for (int i = n - 1; i >= 0; --i) b.push_back(static_cast<u8>(v >> (8 * i)));
}
inline u64 get(Span s, std::size_t off, int n) {
    u64 v = 0;
    for (int i = 0; i < n; ++i) v = (v << 8) | s[off + i];
    return v;
}
inline void put_alpha(Bytes& b, std::string_view s, std::size_t n) {
    for (std::size_t i = 0; i < n; ++i) b.push_back(i < s.size() ? static_cast<u8>(s[i]) : static_cast<u8>(' '));
}
inline std::string get_alpha(Span s, std::size_t off, std::size_t n) {
    std::string r(reinterpret_cast<const char*>(s.data() + off), n);
    while (!r.empty() && r.back() == ' ') r.pop_back();
    return r;
}

struct Alpha8 {                       // fixed-width symbol without allocation
    std::array<char, 8> c{};
    Alpha8() { c.fill(' '); }
    explicit Alpha8(std::string_view s) {
        c.fill(' ');
        for (std::size_t i = 0; i < s.size() && i < 8; ++i) c[i] = s[i];
    }
    std::string str() const {
        std::string r(c.data(), 8);
        while (!r.empty() && r.back() == ' ') r.pop_back();
        return r;
    }
    bool operator==(const Alpha8&) const = default;
};

// ---------------------------------------------------------------------------------------------- feed
struct Feed {
    char type{};
    u16 locate{}, tracking{};
    u64 ts{};                          // 48-bit on the wire
    u64 ref{}, new_ref{}, match{}, seq{};
    char side{' '}, printable{' '}, cross_type{' '}, direction{' '}, variation{' '}, event{' '}, state{' '},
        reserved{' '}, matching{' '};
    u64 shares{};                      // u32 on the wire except in Q (u64)
    Alpha8 stock;
    u32 price{}, far{}, nearp{}, ref_price{}, tick{}, lot{}, orders{}, crc{};
    u64 paired{}, imbalance{};
    std::array<char, 4> reason{' ', ' ', ' ', ' '};
};

inline std::size_t feed_length(char t) {
    switch (t) {
        case 'A': return 36; case 'E': return 31; case 'X': return 23; case 'D': return 19; case 'P': return 44;
        case 'U': return 35; case 'C': return 36; case 'Q': return 40; case 'I': return 50; case 'S': return 12;
        case 'H': return 25; case 'R': return 28; case 'G': return 23; case 'W': return 23; default: return 0;
    }
}

inline void encode(Bytes& b, const Feed& m) {
    b.push_back(static_cast<u8>(m.type));
    put(b, m.locate, 2);
    put(b, m.tracking, 2);
    put(b, m.ts, 6);
    auto a8 = [&](const Alpha8& x) { for (char ch : x.c) b.push_back(static_cast<u8>(ch)); };
    switch (m.type) {
        case 'A': put(b, m.ref, 8); b.push_back(m.side); put(b, m.shares, 4); a8(m.stock); put(b, m.price, 4); break;
        case 'E': put(b, m.ref, 8); put(b, m.shares, 4); put(b, m.match, 8); break;
        case 'X': put(b, m.ref, 8); put(b, m.shares, 4); break;
        case 'D': put(b, m.ref, 8); break;
        case 'P': put(b, m.ref, 8); b.push_back(m.side); put(b, m.shares, 4); a8(m.stock); put(b, m.price, 4);
                  put(b, m.match, 8); break;
        case 'U': put(b, m.ref, 8); put(b, m.new_ref, 8); put(b, m.shares, 4); put(b, m.price, 4); break;
        case 'C': put(b, m.ref, 8); put(b, m.shares, 4); put(b, m.match, 8); b.push_back(m.printable);
                  put(b, m.price, 4); break;
        case 'Q': put(b, m.shares, 8); a8(m.stock); put(b, m.price, 4); put(b, m.match, 8); b.push_back(m.cross_type); break;
        case 'I': put(b, m.paired, 8); put(b, m.imbalance, 8); b.push_back(m.direction); a8(m.stock);
                  put(b, m.far, 4); put(b, m.nearp, 4); put(b, m.ref_price, 4); b.push_back(m.cross_type);
                  b.push_back(m.variation); break;
        case 'S': b.push_back(m.event); break;
        case 'H': a8(m.stock); b.push_back(m.state); b.push_back(m.reserved);
                  for (char ch : m.reason) b.push_back(static_cast<u8>(ch));
                  break;
        case 'R': a8(m.stock); put(b, m.tick, 4); put(b, m.lot, 4); b.push_back(m.matching); break;
        case 'G': put(b, m.seq, 8); put(b, m.orders, 4); break;
        case 'W': put(b, m.seq, 8); put(b, m.crc, 4); break;
        default: throw std::runtime_error("unknown feed type");
    }
}

inline Feed decode_feed(Span s) {
    Feed m;
    if (s.empty()) throw std::runtime_error("empty message");
    m.type = static_cast<char>(s[0]);
    if (feed_length(m.type) == 0 || s.size() != feed_length(m.type)) throw std::runtime_error("bad feed length");
    m.locate = static_cast<u16>(get(s, 1, 2));
    m.tracking = static_cast<u16>(get(s, 3, 2));
    m.ts = get(s, 5, 6);
    auto a8 = [&](std::size_t off) { Alpha8 x; std::memcpy(x.c.data(), s.data() + off, 8); return x; };
    switch (m.type) {
        case 'A': m.ref = get(s, 11, 8); m.side = static_cast<char>(s[19]); m.shares = get(s, 20, 4); m.stock = a8(24);
                  m.price = static_cast<u32>(get(s, 32, 4)); break;
        case 'E': m.ref = get(s, 11, 8); m.shares = get(s, 19, 4); m.match = get(s, 23, 8); break;
        case 'X': m.ref = get(s, 11, 8); m.shares = get(s, 19, 4); break;
        case 'D': m.ref = get(s, 11, 8); break;
        case 'P': m.ref = get(s, 11, 8); m.side = static_cast<char>(s[19]); m.shares = get(s, 20, 4); m.stock = a8(24);
                  m.price = static_cast<u32>(get(s, 32, 4)); m.match = get(s, 36, 8); break;
        case 'U': m.ref = get(s, 11, 8); m.new_ref = get(s, 19, 8); m.shares = get(s, 27, 4);
                  m.price = static_cast<u32>(get(s, 31, 4)); break;
        case 'C': m.ref = get(s, 11, 8); m.shares = get(s, 19, 4); m.match = get(s, 23, 8);
                  m.printable = static_cast<char>(s[31]); m.price = static_cast<u32>(get(s, 32, 4)); break;
        case 'Q': m.shares = get(s, 11, 8); m.stock = a8(19); m.price = static_cast<u32>(get(s, 27, 4));
                  m.match = get(s, 31, 8); m.cross_type = static_cast<char>(s[39]); break;
        case 'I': m.paired = get(s, 11, 8); m.imbalance = get(s, 19, 8); m.direction = static_cast<char>(s[27]);
                  m.stock = a8(28); m.far = static_cast<u32>(get(s, 36, 4)); m.nearp = static_cast<u32>(get(s, 40, 4));
                  m.ref_price = static_cast<u32>(get(s, 44, 4)); m.cross_type = static_cast<char>(s[48]);
                  m.variation = static_cast<char>(s[49]); break;
        case 'S': m.event = static_cast<char>(s[11]); break;
        case 'H': m.stock = a8(11); m.state = static_cast<char>(s[19]); m.reserved = static_cast<char>(s[20]);
                  for (int i = 0; i < 4; ++i) m.reason[i] = static_cast<char>(s[21 + i]);
                  break;
        case 'R': m.stock = a8(11); m.tick = static_cast<u32>(get(s, 19, 4)); m.lot = static_cast<u32>(get(s, 23, 4));
                  m.matching = static_cast<char>(s[27]); break;
        case 'G': m.seq = get(s, 11, 8); m.orders = static_cast<u32>(get(s, 19, 4)); break;
        case 'W': m.seq = get(s, 11, 8); m.crc = static_cast<u32>(get(s, 19, 4)); break;
        default: break;
    }
    return m;
}

// ---------------------------------------------------------------------------------------------- order entry in
struct In {
    char type{};
    u64 cl_ord_id{}, new_cl_ord_id{}, quote_id{};
    u16 locate{}, stp_group{};
    char side{'B'}, tif{'D'}, display{'Y'}, post_only{'N'}, stp_mode{'N'};
    u32 qty{}, price{}, display_qty{}, min_qty{}, stop_price{}, leave_qty{}, bid_price{}, bid_qty{}, ask_price{},
        ask_qty{};
};

inline std::size_t in_length(char t) {
    switch (t) { case 'O': return 38; case 'U': return 25; case 'X': return 13; case 'M': return 4; case 'Q': return 27;
                 default: return 0; }
}

inline void encode(Bytes& b, const In& m) {
    b.push_back(static_cast<u8>(m.type));
    switch (m.type) {
        case 'O': put(b, m.cl_ord_id, 8); put(b, m.locate, 2); b.push_back(m.side); put(b, m.qty, 4); put(b, m.price, 4);
                  b.push_back(m.tif); b.push_back(m.display); b.push_back(m.post_only); put(b, m.display_qty, 4);
                  put(b, m.min_qty, 4); put(b, m.stp_group, 2); b.push_back(m.stp_mode); put(b, m.stop_price, 4); break;
        case 'U': put(b, m.cl_ord_id, 8); put(b, m.new_cl_ord_id, 8); put(b, m.qty, 4); put(b, m.price, 4); break;
        case 'X': put(b, m.cl_ord_id, 8); put(b, m.leave_qty, 4); break;
        case 'M': put(b, m.locate, 2); b.push_back(m.side); break;
        case 'Q': put(b, m.quote_id, 8); put(b, m.locate, 2); put(b, m.bid_price, 4); put(b, m.bid_qty, 4);
                  put(b, m.ask_price, 4); put(b, m.ask_qty, 4); break;
        default: throw std::runtime_error("unknown inbound type");
    }
}

inline In decode_in(Span s) {
    In m;
    if (s.empty()) throw std::runtime_error("empty message");
    m.type = static_cast<char>(s[0]);
    if (in_length(m.type) == 0 || s.size() != in_length(m.type)) throw std::runtime_error("bad inbound length");
    auto c = [&](std::size_t i) { return static_cast<char>(s[i]); };
    auto u = [&](std::size_t o, int n) { return static_cast<u32>(get(s, o, n)); };
    switch (m.type) {
        case 'O': m.cl_ord_id = get(s, 1, 8); m.locate = static_cast<u16>(get(s, 9, 2)); m.side = c(11); m.qty = u(12, 4);
                  m.price = u(16, 4); m.tif = c(20); m.display = c(21); m.post_only = c(22); m.display_qty = u(23, 4);
                  m.min_qty = u(27, 4); m.stp_group = static_cast<u16>(get(s, 31, 2)); m.stp_mode = c(33);
                  m.stop_price = u(34, 4); break;
        case 'U': m.cl_ord_id = get(s, 1, 8); m.new_cl_ord_id = get(s, 9, 8); m.qty = u(17, 4); m.price = u(21, 4); break;
        case 'X': m.cl_ord_id = get(s, 1, 8); m.leave_qty = u(9, 4); break;
        case 'M': m.locate = static_cast<u16>(get(s, 1, 2)); m.side = c(3); break;
        case 'Q': m.quote_id = get(s, 1, 8); m.locate = static_cast<u16>(get(s, 9, 2)); m.bid_price = u(11, 4);
                  m.bid_qty = u(15, 4); m.ask_price = u(19, 4); m.ask_qty = u(23, 4); break;
        default: break;
    }
    return m;
}

// ---------------------------------------------------------------------------------------------- order entry out
struct Out {
    char type{};
    u64 ts{}, cl_ord_id{}, new_cl_ord_id{}, ref{}, match{};
    u16 locate{};
    char side{' '}, tif{' '}, display{' '}, state{' '}, priority{' '}, reason{' '}, liquidity{' '}, event{' '};
    u32 qty{}, price{}, decrement{}, leaves{};
    i64 fee{};
};

inline std::size_t out_length(char t) {
    switch (t) { case 'S': return 10; case 'A': return 39; case 'U': return 42; case 'C': return 22; case 'E': return 46;
                 case 'J': return 18; default: return 0; }
}

inline void encode(Bytes& b, const Out& m) {
    b.push_back(static_cast<u8>(m.type));
    put(b, m.ts, 8);
    switch (m.type) {
        case 'S': b.push_back(m.event); break;
        case 'A': put(b, m.cl_ord_id, 8); put(b, m.ref, 8); put(b, m.locate, 2); b.push_back(m.side); put(b, m.qty, 4);
                  put(b, m.price, 4); b.push_back(m.tif); b.push_back(m.display); b.push_back(m.state); break;
        case 'U': put(b, m.cl_ord_id, 8); put(b, m.new_cl_ord_id, 8); put(b, m.ref, 8); put(b, m.qty, 4);
                  put(b, m.price, 4); b.push_back(m.priority); break;
        case 'C': put(b, m.cl_ord_id, 8); put(b, m.decrement, 4); b.push_back(m.reason); break;
        case 'E': put(b, m.cl_ord_id, 8); put(b, m.qty, 4); put(b, m.price, 4); put(b, m.match, 8);
                  b.push_back(m.liquidity); put(b, static_cast<u64>(m.fee), 8); put(b, m.leaves, 4); break;
        case 'J': put(b, m.cl_ord_id, 8); b.push_back(m.reason); break;
        default: throw std::runtime_error("unknown outbound type");
    }
}

inline Out decode_out(Span s) {
    Out m;
    if (s.empty()) throw std::runtime_error("empty message");
    m.type = static_cast<char>(s[0]);
    if (out_length(m.type) == 0 || s.size() != out_length(m.type)) throw std::runtime_error("bad outbound length");
    m.ts = get(s, 1, 8);
    auto c = [&](std::size_t i) { return static_cast<char>(s[i]); };
    auto u = [&](std::size_t o) { return static_cast<u32>(get(s, o, 4)); };
    switch (m.type) {
        case 'S': m.event = c(9); break;
        case 'A': m.cl_ord_id = get(s, 9, 8); m.ref = get(s, 17, 8); m.locate = static_cast<u16>(get(s, 25, 2));
                  m.side = c(27); m.qty = u(28); m.price = u(32); m.tif = c(36); m.display = c(37); m.state = c(38); break;
        case 'U': m.cl_ord_id = get(s, 9, 8); m.new_cl_ord_id = get(s, 17, 8); m.ref = get(s, 25, 8); m.qty = u(33);
                  m.price = u(37); m.priority = c(41); break;
        case 'C': m.cl_ord_id = get(s, 9, 8); m.decrement = u(17); m.reason = c(21); break;
        case 'E': m.cl_ord_id = get(s, 9, 8); m.qty = u(17); m.price = u(21); m.match = get(s, 25, 8); m.liquidity = c(33);
                  m.fee = static_cast<i64>(get(s, 34, 8)); m.leaves = u(42); break;
        case 'J': m.cl_ord_id = get(s, 9, 8); m.reason = c(17); break;
        default: break;
    }
    return m;
}

// ---------------------------------------------------------------------------------------------- control (journal)
struct Ctl {
    char type{};
    u16 session{}, locate{};
    u32 firm{}, ref_price{}, band_lo{}, band_hi{}, bid{}, ask{};
    char cod{'N'}, phase{' '}, cross_type{' '}, tif{' '}, freeze{'N'}, event{' '};
    std::array<char, 4> reason{' ', ' ', ' ', ' '};
};

inline std::size_t ctl_length(char t) {
    switch (t) { case 'L': return 8; case 'D': return 3; case 'P': return 8; case 'X': return 4; case 'I': return 4;
                 case 'R': return 15; case 'E': return 4; case 'F': return 4; case 'S': return 2; case 'N': return 11;
                 default: return 0; }
}

inline void encode(Bytes& b, const Ctl& m) {
    b.push_back(static_cast<u8>(m.type));
    switch (m.type) {
        case 'L': put(b, m.session, 2); put(b, m.firm, 4); b.push_back(m.cod); break;
        case 'D': put(b, m.session, 2); break;
        case 'P': put(b, m.locate, 2); b.push_back(m.phase); for (char ch : m.reason) b.push_back(static_cast<u8>(ch)); break;
        case 'X': case 'I': put(b, m.locate, 2); b.push_back(m.cross_type); break;
        case 'R': put(b, m.locate, 2); put(b, m.ref_price, 4); put(b, m.band_lo, 4); put(b, m.band_hi, 4); break;
        case 'E': put(b, m.locate, 2); b.push_back(m.tif); break;
        case 'F': put(b, m.locate, 2); b.push_back(m.freeze); break;
        case 'S': b.push_back(m.event); break;
        case 'N': put(b, m.locate, 2); put(b, m.bid, 4); put(b, m.ask, 4); break;
        default: throw std::runtime_error("unknown control type");
    }
}

inline Ctl decode_ctl(Span s) {
    Ctl m;
    if (s.empty()) throw std::runtime_error("empty message");
    m.type = static_cast<char>(s[0]);
    if (ctl_length(m.type) == 0 || s.size() != ctl_length(m.type)) throw std::runtime_error("bad control length");
    auto c = [&](std::size_t i) { return static_cast<char>(s[i]); };
    switch (m.type) {
        case 'L': m.session = static_cast<u16>(get(s, 1, 2)); m.firm = static_cast<u32>(get(s, 3, 4)); m.cod = c(7); break;
        case 'D': m.session = static_cast<u16>(get(s, 1, 2)); break;
        case 'P': m.locate = static_cast<u16>(get(s, 1, 2)); m.phase = c(3); for (int i = 0; i < 4; ++i) m.reason[i] = c(4 + i);
                  break;
        case 'X': case 'I': m.locate = static_cast<u16>(get(s, 1, 2)); m.cross_type = c(3); break;
        case 'R': m.locate = static_cast<u16>(get(s, 1, 2)); m.ref_price = static_cast<u32>(get(s, 3, 4));
                  m.band_lo = static_cast<u32>(get(s, 7, 4)); m.band_hi = static_cast<u32>(get(s, 11, 4)); break;
        case 'E': m.locate = static_cast<u16>(get(s, 1, 2)); m.tif = c(3); break;
        case 'F': m.locate = static_cast<u16>(get(s, 1, 2)); m.freeze = c(3); break;
        case 'S': m.event = c(1); break;
        case 'N': m.locate = static_cast<u16>(get(s, 1, 2)); m.bid = static_cast<u32>(get(s, 3, 4));
                  m.ask = static_cast<u32>(get(s, 7, 4)); break;
        default: break;
    }
    return m;
}

// ---------------------------------------------------------------------------------------------- framing
struct JournalRecord {
    u64 t_ns;
    u16 session;
    Span payload;
};

// Calls f(record) for every journal record in `data`.
template <class F>
void for_each_record(Span data, F&& f) {
    std::size_t i = 0;
    while (i + 12 <= data.size()) {
        const u64 t = get(data, i, 8);
        const u16 s = static_cast<u16>(get(data, i + 8, 2));
        const std::size_t n = static_cast<std::size_t>(get(data, i + 10, 2));
        if (i + 12 + n > data.size()) throw std::runtime_error("truncated journal");
        f(JournalRecord{t, s, data.subspan(i + 12, n)});
        i += 12 + n;
    }
}

inline void journal_record(Bytes& b, u64 t_ns, u16 session, const Bytes& payload) {
    put(b, t_ns, 8);
    put(b, session, 2);
    put(b, payload.size(), 2);
    b.insert(b.end(), payload.begin(), payload.end());
}

// MoldUDP64: session alpha10 | seq u64 | count u16 | (u16 len | message)*
inline Bytes mold_packet(std::string_view session, u64 seq, const std::vector<Bytes>& msgs) {
    Bytes b;
    put_alpha(b, session, 10);
    put(b, seq, 8);
    put(b, msgs.size(), 2);
    for (const auto& m : msgs) { put(b, m.size(), 2); b.insert(b.end(), m.begin(), m.end()); }
    return b;
}

struct MoldHeader {
    std::string session;
    u64 seq;
    u16 count;
};

// Parses a packet; calls f(seq_of_message, message span) for each message. Returns the header.
template <class F>
MoldHeader mold_parse(Span p, F&& f) {
    if (p.size() < 20) throw std::runtime_error("short MoldUDP64 packet");
    MoldHeader h{get_alpha(p, 0, 10), get(p, 10, 8), static_cast<u16>(get(p, 18, 2))};
    if (h.count == 0 || h.count == 0xFFFF) return h;
    std::size_t i = 20;
    for (u16 k = 0; k < h.count; ++k) {
        if (i + 2 > p.size()) throw std::runtime_error("truncated MoldUDP64 packet");
        const std::size_t n = static_cast<std::size_t>(get(p, i, 2));
        if (i + 2 + n > p.size()) throw std::runtime_error("truncated MoldUDP64 message");
        f(h.seq + k, p.subspan(i + 2, n));
        i += 2 + n;
    }
    return h;
}

// SoupBinTCP 4.0 frame: u16 length (type byte included) | type | payload
inline Bytes soup_frame(char type, Span payload = {}) {
    Bytes b;
    put(b, payload.size() + 1, 2);
    b.push_back(static_cast<u8>(type));
    b.insert(b.end(), payload.begin(), payload.end());
    return b;
}

inline std::string num20(u64 v) {
    std::string s = std::to_string(v);
    return std::string(20 - s.size(), ' ') + s;
}

inline u32 crc32(Span data) {
    u32 c = 0xFFFFFFFFu;
    for (u8 byte : data) {
        c ^= byte;
        for (int k = 0; k < 8; ++k) c = (c >> 1) ^ (0xEDB88320u & (0u - (c & 1u)));
    }
    return ~c;
}

}  // namespace firm::exchsim
