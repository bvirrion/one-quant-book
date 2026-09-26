// firm.simdscan -- byte-class scanning and integer / fixed-point parsing with vector instructions (build of One Quant
// Book 13, chapter 14). Every vector routine has a scalar reference that returns the same result for every input,
// and the public entry points choose the widest implementation the running CPU supports, once, at the first call.
// No routine reads a byte past p + n: the vector loops stop at the last full block and a scalar tail finishes.
// Consumers: firm.fixengine (tag=value fields split on SOH), firm.wsclient (JSON structural characters).
#pragma once
#include <immintrin.h>

#include <cstddef>
#include <cstdint>
#include <cstring>

namespace firm::simdscan {

// ---- scalar references ------------------------------------------------------------------------------------------
inline std::size_t find_byte_scalar(const char* p, std::size_t n, char c) {
    for (std::size_t i = 0; i < n; ++i)
        if (p[i] == c) return i;
    return n;
}

inline std::size_t positions_scalar(const char* p, std::size_t n, char c, std::uint32_t* out, std::size_t cap) {
    std::size_t k = 0;
    for (std::size_t i = 0; i < n && k < cap; ++i)
        if (p[i] == c) out[k++] = static_cast<std::uint32_t>(i);
    return k;
}

inline bool in_set(char b, const char* set, std::size_t m) {
    for (std::size_t j = 0; j < m; ++j)
        if (b == set[j]) return true;
    return false;
}

inline std::size_t positions_any_scalar(const char* p, std::size_t n, const char* set, std::size_t m,
                                        std::uint32_t* out, std::size_t cap) {
    std::size_t k = 0;
    for (std::size_t i = 0; i < n && k < cap; ++i)
        if (in_set(p[i], set, m)) out[k++] = static_cast<std::uint32_t>(i);
    return k;
}

// ---- SSE2 (every x86-64 CPU has it) -------------------------------------------------------------------------------
// Full 16-byte blocks, then one last block that ends exactly at p + n and overlaps the previous one: its bytes
// already checked are shifted out of the mask. Messages shorter than a block go to the scalar loop.
inline std::size_t find_byte_sse2(const char* p, std::size_t n, char c) {
    if (n < 16) return find_byte_scalar(p, n, c);
    const __m128i needle = _mm_set1_epi8(c);
    std::size_t i = 0;
    for (; i + 16 <= n; i += 16) {
        const __m128i v = _mm_loadu_si128(reinterpret_cast<const __m128i*>(p + i));
        const unsigned m = static_cast<unsigned>(_mm_movemask_epi8(_mm_cmpeq_epi8(v, needle)));
        if (m != 0) return i + static_cast<std::size_t>(__builtin_ctz(m));
    }
    if (i < n) {
        const __m128i v = _mm_loadu_si128(reinterpret_cast<const __m128i*>(p + n - 16));
        const unsigned m = static_cast<unsigned>(_mm_movemask_epi8(_mm_cmpeq_epi8(v, needle))) >> (i - (n - 16));
        if (m != 0) return i + static_cast<std::size_t>(__builtin_ctz(m));
    }
    return n;
}

// ---- AVX2: 32 bytes per compare -----------------------------------------------------------------------------------
__attribute__((target("avx2"))) inline std::size_t find_byte_avx2(const char* p, std::size_t n, char c) {
    if (n < 32) return find_byte_sse2(p, n, c);
    const __m256i needle = _mm256_set1_epi8(c);
    std::size_t i = 0;
    for (; i + 32 <= n; i += 32) {
        const __m256i v = _mm256_loadu_si256(reinterpret_cast<const __m256i*>(p + i));
        const unsigned m = static_cast<unsigned>(_mm256_movemask_epi8(_mm256_cmpeq_epi8(v, needle)));
        if (m != 0) return i + static_cast<std::size_t>(__builtin_ctz(m));
    }
    if (i < n) {   // the last, overlapping block
        const __m256i v = _mm256_loadu_si256(reinterpret_cast<const __m256i*>(p + n - 32));
        const unsigned m = static_cast<unsigned>(_mm256_movemask_epi8(_mm256_cmpeq_epi8(v, needle))) >> (i - (n - 32));
        if (m != 0) return i + static_cast<std::size_t>(__builtin_ctz(m));
    }
    return n;
}

// Every position of c: one compare and one mask per 32 bytes, then one trailing-zero count per match.
__attribute__((target("avx2,bmi"))) inline std::size_t positions_avx2(const char* p, std::size_t n, char c,
                                                                      std::uint32_t* out, std::size_t cap) {
    if (n < 32) return positions_scalar(p, n, c, out, cap);
    const __m256i needle = _mm256_set1_epi8(c);
    std::size_t k = 0;
    for (std::size_t i = 0; i < n; i += 32) {
        const std::size_t at = i + 32 <= n ? i : n - 32;       // the last block overlaps the previous one
        const __m256i v = _mm256_loadu_si256(reinterpret_cast<const __m256i*>(p + at));
        unsigned m = static_cast<unsigned>(_mm256_movemask_epi8(_mm256_cmpeq_epi8(v, needle))) >> (i - at);
        while (m != 0 && k < cap) {
            out[k++] = static_cast<std::uint32_t>(i + static_cast<std::size_t>(__builtin_ctz(m)));
            m &= m - 1;   // clear the lowest set bit
        }
    }
    return k;
}

// Positions of any byte of a small set (JSON's structural characters, say): one compare per set member, OR-ed.
__attribute__((target("avx2,bmi"))) inline std::size_t positions_any_avx2(const char* p, std::size_t n,
                                                                          const char* set, std::size_t m,
                                                                          std::uint32_t* out, std::size_t cap) {
    if (n < 32) return positions_any_scalar(p, n, set, m, out, cap);
    std::size_t k = 0;
    for (std::size_t i = 0; i < n; i += 32) {
        const std::size_t at = i + 32 <= n ? i : n - 32;
        const __m256i v = _mm256_loadu_si256(reinterpret_cast<const __m256i*>(p + at));
        __m256i hit = _mm256_setzero_si256();
        for (std::size_t j = 0; j < m; ++j) hit = _mm256_or_si256(hit, _mm256_cmpeq_epi8(v, _mm256_set1_epi8(set[j])));
        unsigned mask = static_cast<unsigned>(_mm256_movemask_epi8(hit)) >> (i - at);
        while (mask != 0 && k < cap) {
            out[k++] = static_cast<std::uint32_t>(i + static_cast<std::size_t>(__builtin_ctz(mask)));
            mask &= mask - 1;
        }
    }
    return k;
}

// ---- eight ASCII digits at once -----------------------------------------------------------------------------------
inline std::uint32_t parse8_scalar(const char* p) {
    std::uint32_t v = 0;
    for (int i = 0; i < 8; ++i) v = v * 10 + static_cast<std::uint32_t>(p[i] - '0');
    return v;
}

// True when all eight bytes are '0'..'9'.
inline bool is8digits(const char* p) {
    std::uint64_t v;
    std::memcpy(&v, p, 8);
    return (((v & 0xF0F0F0F0F0F0F0F0ULL) | (((v + 0x0606060606060606ULL) & 0xF0F0F0F0F0F0F0F0ULL) >> 4)) ==
            0x3333333333333333ULL);
}

// SIMD within a register: the first digit is the lowest byte (little-endian load). Combine neighbouring digits into
// 2-digit numbers in 16-bit lanes, those into 4-digit numbers in 32-bit lanes, and those into the 8-digit result.
inline std::uint32_t parse8_swar(const char* p) {
    std::uint64_t v;
    std::memcpy(&v, p, 8);
    v -= 0x3030303030303030ULL;                               // '0' from every byte
    v = (v * 10 + (v >> 8)) & 0x00FF00FF00FF00FFULL;         // d0*10 + d1, ...
    v = (v * 100 + (v >> 16)) & 0x0000FFFF0000FFFFULL;       // (d0d1)*100 + d2d3, ...
    v = (v * 10000 + (v >> 32)) & 0xFFFFFFFFULL;             // (d0..d3)*10000 + d4..d7
    return static_cast<std::uint32_t>(v);
}

// The same with SSSE3/SSE4.1 multiply-adds: bytes x (10,1) -> pairs, pairs x (100,1) -> quads, pack, x (10000,1).
__attribute__((target("ssse3,sse4.1"))) inline std::uint32_t parse8_sse(const char* p) {
    const __m128i d = _mm_sub_epi8(_mm_loadl_epi64(reinterpret_cast<const __m128i*>(p)), _mm_set1_epi8('0'));
    const __m128i pairs = _mm_maddubs_epi16(d, _mm_setr_epi8(10, 1, 10, 1, 10, 1, 10, 1, 0, 0, 0, 0, 0, 0, 0, 0));
    const __m128i quads = _mm_madd_epi16(pairs, _mm_setr_epi16(100, 1, 100, 1, 0, 0, 0, 0));
    const __m128i packed = _mm_packus_epi32(quads, quads);
    const __m128i eight = _mm_madd_epi16(packed, _mm_setr_epi16(10000, 1, 0, 0, 0, 0, 0, 0));
    return static_cast<std::uint32_t>(_mm_cvtsi128_si32(eight));
}

// An unsigned integer of up to 19 digits starting at p (stops at the first non-digit or at n); eight at a time.
inline bool parse_uint(const char* p, std::size_t n, std::uint64_t& value, std::size_t& used) {
    std::uint64_t v = 0;
    std::size_t i = 0;
    while (i + 8 <= n && i + 8 <= 19 && is8digits(p + i)) {
        v = v * 100000000ULL + parse8_swar(p + i);
        i += 8;
    }
    while (i < n && i < 19 && p[i] >= '0' && p[i] <= '9') v = v * 10 + static_cast<std::uint64_t>(p[i++] - '0');
    value = v;
    used = i;
    return i > 0;
}

// A decimal price "123.4567" as an integer number of 10^-scale units (123.4567 with scale 6 -> 123456700); false on
// an empty integer part, on more than `scale` decimals, or on trailing garbage. The caller keeps the value in range
// (scale <= 9 and at most 9 integer digits never overflow).
inline bool parse_fixed(const char* p, std::size_t n, int scale, std::int64_t& out) {
    bool neg = n > 0 && p[0] == '-';
    std::size_t i = neg ? 1 : 0, used = 0;
    std::uint64_t ip = 0, fp = 0;
    if (!parse_uint(p + i, n - i, ip, used)) return false;
    i += used;
    int decimals = 0;
    if (i < n && p[i] == '.') {
        ++i;
        parse_uint(p + i, n - i, fp, used);   // "123." has no decimals, and is accepted
        decimals = static_cast<int>(used);
        i += used;
    }
    if (i != n || decimals > scale) return false;
    for (int d = decimals; d < scale; ++d) fp *= 10;
    std::uint64_t unit = 1;
    for (int d = 0; d < scale; ++d) unit *= 10;
    const auto v = static_cast<std::int64_t>(ip * unit + fp);
    out = neg ? -v : v;
    return true;
}

// ---- dispatch: the widest implementation this CPU runs, chosen once -----------------------------------------------
enum class Level { scalar, sse2, avx2 };

inline Level detect() {
    __builtin_cpu_init();
    return __builtin_cpu_supports("avx2") && __builtin_cpu_supports("bmi") ? Level::avx2 : Level::sse2;
}

inline Level level() {
    static const Level l = detect();
    return l;
}

inline std::size_t find_byte(const char* p, std::size_t n, char c) {
    return level() == Level::avx2 ? find_byte_avx2(p, n, c) : find_byte_sse2(p, n, c);
}

inline std::size_t positions(const char* p, std::size_t n, char c, std::uint32_t* out, std::size_t cap) {
    return level() == Level::avx2 ? positions_avx2(p, n, c, out, cap) : positions_scalar(p, n, c, out, cap);
}

inline std::size_t positions_any(const char* p, std::size_t n, const char* set, std::size_t m, std::uint32_t* out,
                                 std::size_t cap) {
    return level() == Level::avx2 ? positions_any_avx2(p, n, set, m, out, cap)
                                  : positions_any_scalar(p, n, set, m, out, cap);
}

}  // namespace firm::simdscan
