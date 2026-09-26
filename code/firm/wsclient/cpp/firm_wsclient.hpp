// firm.wsclient -- WebSocket frames, depth updates through a structural index, and HMAC-SHA-256 request signing, in
// C++20 (build of One Quant Book 13, chapter 17). Same results as the Python reference on the shared fixtures.
#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <string>
#include <string_view>

#include "../../simdscan/cpp/firm_simdscan.hpp"

namespace firm::ws {

// ---- frames (RFC 6455, section 5.2) -----------------------------------------------------------------------------
enum Op : std::uint8_t { kCont = 0x0, kText = 0x1, kBinary = 0x2, kClose = 0x8, kPing = 0x9, kPong = 0xA };
enum class FrameError { ok, incomplete, reserved_bits, length_encoding, bad_control };

struct FrameView {
    bool fin = false, masked = false;
    std::uint8_t opcode = 0;
    std::uint8_t key[4] = {0, 0, 0, 0};
    std::uint8_t* payload = nullptr;   // unmasked in place by decode_frame
    std::size_t len = 0;
};

// XOR with the 4-byte key, eight bytes at a time (the key repeated twice in a 64-bit word), then the tail.
inline void unmask(std::uint8_t* p, std::size_t n, const std::uint8_t key[4]) {
    std::uint64_t k8;
    std::uint8_t kk[8] = {key[0], key[1], key[2], key[3], key[0], key[1], key[2], key[3]};
    std::memcpy(&k8, kk, 8);
    std::size_t i = 0;
    for (; i + 8 <= n; i += 8) {
        std::uint64_t w;
        std::memcpy(&w, p + i, 8);
        w ^= k8;
        std::memcpy(p + i, &w, 8);
    }
    for (; i < n; ++i) p[i] ^= key[i % 4];
}

// Decodes one frame at p (unmasking its payload in place); returns the bytes used, 0 if incomplete or invalid.
inline std::size_t decode_frame(std::uint8_t* p, std::size_t n, FrameView& f, FrameError& err) {
    err = FrameError::incomplete;
    if (n < 2) return 0;
    if (p[0] & 0x70) { err = FrameError::reserved_bits; return 0; }
    f.fin = (p[0] & 0x80) != 0;
    f.opcode = p[0] & 0x0F;
    f.masked = (p[1] & 0x80) != 0;
    std::uint64_t len = p[1] & 0x7F;
    std::size_t i = 2;
    if (len == 126) {
        if (n < 4) return 0;
        len = (std::uint64_t{p[2]} << 8) | p[3];
        i = 4;
        if (len < 126) { err = FrameError::length_encoding; return 0; }
    } else if (len == 127) {
        if (n < 10) return 0;
        len = 0;
        for (int k = 0; k < 8; ++k) len = (len << 8) | p[2 + k];
        i = 10;
        if (len <= 0xFFFF || (len >> 63) != 0) { err = FrameError::length_encoding; return 0; }
    }
    if (f.opcode >= 0x8 && (len > 125 || !f.fin)) { err = FrameError::bad_control; return 0; }
    if (f.masked) {
        if (n < i + 4) return 0;
        std::memcpy(f.key, p + i, 4);
        i += 4;
    }
    if (n < i + len) return 0;
    f.payload = p + i;
    f.len = static_cast<std::size_t>(len);
    if (f.masked) unmask(f.payload, f.len, f.key);
    err = FrameError::ok;
    return i + f.len;
}

// Writes a frame into out (room for len + 14 bytes); a client passes a masking key, a server does not.
inline std::size_t encode_frame(std::uint8_t* out, const std::uint8_t* payload, std::size_t len, std::uint8_t opcode,
                                bool fin = true, const std::uint8_t* key = nullptr) {
    std::size_t i = 0;
    out[i++] = static_cast<std::uint8_t>((fin ? 0x80 : 0) | opcode);
    const std::uint8_t m = key ? 0x80 : 0;
    if (len <= 125) {
        out[i++] = static_cast<std::uint8_t>(m | len);
    } else if (len <= 0xFFFF) {
        out[i++] = m | 126;
        out[i++] = static_cast<std::uint8_t>(len >> 8);
        out[i++] = static_cast<std::uint8_t>(len);
    } else {
        out[i++] = m | 127;
        for (int k = 7; k >= 0; --k) out[i++] = static_cast<std::uint8_t>(static_cast<std::uint64_t>(len) >> (8 * k));
    }
    if (key) {
        std::memcpy(out + i, key, 4);
        i += 4;
    }
    std::memcpy(out + i, payload, len);
    if (key) unmask(out + i, len, key);
    return i + len;
}

// Joins fragmented data messages; control frames pass through. Fragmented messages are rare and copied; a message in
// one frame is returned as a view of the frame.
class Reassembler {
public:
    // Returns true when `msg` holds a complete message (opcode in `op`).
    bool feed(const FrameView& f, std::uint8_t& op, std::string_view& msg) {
        if (f.opcode >= 0x8 || (f.fin && f.opcode != kCont && op_ < 0)) {
            op = f.opcode;
            msg = {reinterpret_cast<const char*>(f.payload), f.len};
            return true;
        }
        if (f.opcode != kCont) {
            op_ = f.opcode;
            buf_.clear();
        }
        buf_.append(reinterpret_cast<const char*>(f.payload), f.len);
        if (!f.fin) return false;
        op = static_cast<std::uint8_t>(op_);
        msg = buf_;
        op_ = -1;
        return true;
    }

private:
    int op_ = -1;
    std::string buf_;
};

// ---- depth updates through a structural index --------------------------------------------------------------------
struct Level {
    std::int64_t price, qty;   // units of 1e-8
};

struct Depth {
    std::uint64_t event_time = 0, first = 0, last = 0;
    char symbol[16] = {};
    std::array<Level, 64> bids{}, asks{};
    std::size_t nb = 0, na = 0;
};

// Stage 1: the positions of every structural character and quote, by the vector scan of chapter 14. Stage 2: walk
// the index with the shape of the venue's depth message known in advance; no tree, no allocation, no float.
// Returns false on any deviation from the expected shape (the caller falls back to a general parser).
inline bool decode_depth(std::string_view t, Depth& d) {
    static constexpr char kSet[] = {'{', '}', '[', ']', ':', ',', '"'};
    std::uint32_t ix[1024];
    const char* s = t.data();
    const std::size_t m = simdscan::positions_any(s, t.size(), kSet, sizeof kSet, ix, 1024);
    if (m == 1024 || simdscan::find_byte(s, t.size(), '\\') != t.size() || m < 2 || s[ix[0]] != '{') return false;
    std::size_t k = 1;
    auto str = [&](std::string_view& out) {   // a string: two quotes
        if (k + 1 >= m || s[ix[k]] != '"' || s[ix[k + 1]] != '"') return false;
        out = {s + ix[k] + 1, ix[k + 1] - ix[k] - 1};
        k += 2;
        return true;
    };
    auto fixed = [&](std::int64_t& v) {
        std::string_view x;
        return str(x) && simdscan::parse_fixed(x.data(), x.size(), 8, v);
    };
    auto levels = [&](std::array<Level, 64>& out, std::size_t& n) {
        n = 0;
        if (s[ix[k++]] != '[') return false;
        if (s[ix[k]] == ']') { ++k; return true; }
        for (;;) {
            if (n == out.size() || s[ix[k++]] != '[' || !fixed(out[n].price) || s[ix[k++]] != ',' || !fixed(out[n].qty) ||
                s[ix[k++]] != ']')
                return false;
            ++n;
            const char c = s[ix[k++]];
            if (c == ']') return true;
            if (c != ',') return false;
        }
    };
    while (k < m) {
        std::string_view key;
        if (!str(key) || k >= m || s[ix[k++]] != ':') return false;
        if (key == "b" || key == "a") {
            if (!(key == "b" ? levels(d.bids, d.nb) : levels(d.asks, d.na))) return false;
        } else if (s[ix[k]] == '"') {
            std::string_view v;
            if (!str(v)) return false;
            if (key == "s") {
                const std::size_t n = v.size() < sizeof d.symbol - 1 ? v.size() : sizeof d.symbol - 1;
                std::memcpy(d.symbol, v.data(), n);
                d.symbol[n] = 0;
            }
        } else {   // a number: from after ':' to the next ',' or '}'
            const std::size_t a = ix[k - 1] + 1, b = ix[k];
            std::uint64_t v = 0;
            std::size_t used = 0;
            if (!simdscan::parse_uint(s + a, b - a, v, used) || used != b - a) return false;
            if (key == "E") d.event_time = v;
            else if (key == "U") d.first = v;
            else if (key == "u") d.last = v;
        }
        const char c = s[ix[k++]];
        if (c == '}') return k == m;
        if (c != ',') return false;
    }
    return false;
}

// ---- HMAC-SHA-256 (FIPS 180-4 SHA-256; RFC 2104 HMAC with the pads hashed once) -------------------------------------
class Sha256 {
public:
    Sha256() { reset(); }
    void reset() {
        h_ = {0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19};
        n_ = 0;
        fill_ = 0;
    }
    void update(const std::uint8_t* p, std::size_t len) {
        n_ += len;
        if (fill_) {
            const std::size_t k = len < 64 - fill_ ? len : 64 - fill_;
            std::memcpy(buf_ + fill_, p, k);
            fill_ += k;
            p += k;
            len -= k;
            if (fill_ < 64) return;
            block(buf_);
            fill_ = 0;
        }
        for (; len >= 64; p += 64, len -= 64) block(p);
        std::memcpy(buf_, p, len);
        fill_ = len;
    }
    void final(std::uint8_t out[32]) {
        const std::uint64_t bits = n_ * 8;
        const std::uint8_t one = 0x80, zero = 0;
        update(&one, 1);
        while (fill_ != 56) update(&zero, 1);
        std::uint8_t len[8];
        for (int i = 0; i < 8; ++i) len[i] = static_cast<std::uint8_t>(bits >> (56 - 8 * i));
        update(len, 8);
        for (int i = 0; i < 8; ++i)
            for (int j = 0; j < 4; ++j) out[4 * i + j] = static_cast<std::uint8_t>(h_[static_cast<std::size_t>(i)] >> (24 - 8 * j));
    }

private:
    static std::uint32_t rotr(std::uint32_t x, int r) { return (x >> r) | (x << (32 - r)); }
    void block(const std::uint8_t* p) {
        static constexpr std::uint32_t K[64] = {
            0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5, 0xd807aa98,
            0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786,
            0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da, 0x983e5152, 0xa831c66d, 0xb00327c8,
            0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
            0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85, 0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819,
            0xd6990624, 0xf40e3585, 0x106aa070, 0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a,
            0x5b9cca4f, 0x682e6ff3, 0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7,
            0xc67178f2};
        std::uint32_t w[64];
        for (int i = 0; i < 16; ++i)
            w[i] = (std::uint32_t{p[4 * i]} << 24) | (std::uint32_t{p[4 * i + 1]} << 16) | (std::uint32_t{p[4 * i + 2]} << 8) |
                   p[4 * i + 3];
        for (int i = 16; i < 64; ++i) {
            const std::uint32_t s0 = rotr(w[i - 15], 7) ^ rotr(w[i - 15], 18) ^ (w[i - 15] >> 3);
            const std::uint32_t s1 = rotr(w[i - 2], 17) ^ rotr(w[i - 2], 19) ^ (w[i - 2] >> 10);
            w[i] = w[i - 16] + s0 + w[i - 7] + s1;
        }
        std::uint32_t a = h_[0], b = h_[1], c = h_[2], d = h_[3], e = h_[4], f = h_[5], g = h_[6], h = h_[7];
        for (int i = 0; i < 64; ++i) {
            const std::uint32_t t1 = h + (rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25)) + ((e & f) ^ (~e & g)) + K[i] + w[i];
            const std::uint32_t t2 = (rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22)) + ((a & b) ^ (a & c) ^ (b & c));
            h = g; g = f; f = e; e = d + t1; d = c; c = b; b = a; a = t1 + t2;
        }
        h_[0] += a; h_[1] += b; h_[2] += c; h_[3] += d; h_[4] += e; h_[5] += f; h_[6] += g; h_[7] += h;
    }
    std::array<std::uint32_t, 8> h_{};
    std::uint64_t n_ = 0;
    std::uint8_t buf_[64] = {};
    std::size_t fill_ = 0;
};

// The key's inner and outer pads are hashed once, at construction; each signature copies those two states.
class HmacSha256 {
public:
    explicit HmacSha256(std::string_view key) {
        std::uint8_t k[64] = {}, pad[64];
        if (key.size() > 64) {
            Sha256 h;
            h.update(reinterpret_cast<const std::uint8_t*>(key.data()), key.size());
            h.final(k);
        } else {
            std::memcpy(k, key.data(), key.size());
        }
        for (int i = 0; i < 64; ++i) pad[i] = k[i] ^ 0x36;
        inner_.update(pad, 64);
        for (int i = 0; i < 64; ++i) pad[i] = k[i] ^ 0x5c;
        outer_.update(pad, 64);
    }
    void sign(std::string_view msg, std::uint8_t out[32]) const {
        Sha256 in = inner_, o = outer_;
        in.update(reinterpret_cast<const std::uint8_t*>(msg.data()), msg.size());
        std::uint8_t ih[32];
        in.final(ih);
        o.update(ih, 32);
        o.final(out);
    }
    std::string hex(std::string_view msg) const {
        std::uint8_t d[32];
        sign(msg, d);
        static constexpr char x[] = "0123456789abcdef";
        std::string s(64, '0');
        for (int i = 0; i < 32; ++i) {
            s[2 * static_cast<std::size_t>(i)] = x[d[i] >> 4];
            s[2 * static_cast<std::size_t>(i) + 1] = x[d[i] & 15];
        }
        return s;
    }

private:
    Sha256 inner_, outer_;
};

}  // namespace firm::ws
