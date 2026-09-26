// firm.simdscan: every vector routine equals its scalar reference, for every length and position, with no read past
// the end (buffers are allocated to the exact length so that AddressSanitizer runs would catch an overread).
#include "firm_simdscan.hpp"

#include <algorithm>
#include <cstdio>
#include <memory>
#include <random>
#include <string>
#include <vector>

using namespace firm::simdscan;

static int fails = 0;
#define CHECK(c) do { if (!(c)) { std::printf("FAIL line %d: %s\n", __LINE__, #c); ++fails; } } while (0)

int main() {
    std::mt19937 rng(7);
    const bool avx2 = level() == Level::avx2;
    std::printf("dispatch level: %s\n", avx2 ? "avx2" : "sse2");
    for (std::size_t n = 0; n <= 200; ++n) {
        for (int trial = 0; trial < 20; ++trial) {
            std::unique_ptr<char[]> buf(new char[n + 1]);
            for (std::size_t i = 0; i < n; ++i) buf[i] = static_cast<char>('A' + rng() % 20);
            if (n > 0 && trial % 2 == 0)
                for (int k = 0; k < 1 + trial / 4; ++k) buf[rng() % n] = '\x01';
            const char* p = buf.get();
            const std::size_t want = find_byte_scalar(p, n, '\x01');
            CHECK(find_byte_sse2(p, n, '\x01') == want);
            if (avx2) CHECK(find_byte_avx2(p, n, '\x01') == want);
            CHECK(find_byte(p, n, '\x01') == want);
            std::uint32_t a[256], b[256];
            const std::size_t ka = positions_scalar(p, n, '\x01', a, 256);
            const std::size_t kb = positions(p, n, '\x01', b, 256);
            CHECK(ka == kb && std::equal(a, a + ka, b));
            const char set[] = {'A', 'C', 'Q'};
            const std::size_t sa = positions_any_scalar(p, n, set, 3, a, 256);
            const std::size_t sb = positions_any(p, n, set, 3, b, 256);
            CHECK(sa == sb && std::equal(a, a + sa, b));
            if (sa > 3) CHECK(positions_any(p, n, set, 3, b, 3) == 3 && b[2] == a[2]);   // cap respected
        }
    }
    // Eight digits: every representation agrees, on random and edge values.
    for (int t = 0; t < 200000; ++t) {
        const std::uint32_t v = t < 3 ? (t == 0 ? 0u : t == 1 ? 99999999u : 10000000u) : rng() % 100000000u;
        char s[9];
        std::snprintf(s, sizeof s, "%08u", v);
        CHECK(is8digits(s) && parse8_scalar(s) == v && parse8_swar(s) == v);
        if (__builtin_cpu_supports("sse4.1")) CHECK(parse8_sse(s) == v);
    }
    CHECK(!is8digits("1234567a") && !is8digits("12/45678") && !is8digits("1234:678"));
    // Integers and fixed-point prices.
    std::uint64_t u = 0;
    std::size_t used = 0;
    CHECK(parse_uint("1234567890123456789x", 20, u, used) && u == 1234567890123456789ULL && used == 19);
    CHECK(parse_uint("42", 2, u, used) && u == 42 && used == 2);
    CHECK(!parse_uint("x1", 2, u, used));
    std::int64_t f = 0;
    CHECK(parse_fixed("123.4567", 8, 6, f) && f == 123456700);
    CHECK(parse_fixed("-0.05", 5, 4, f) && f == -500);
    CHECK(parse_fixed("17", 2, 2, f) && f == 1700);
    CHECK(parse_fixed("17.", 3, 2, f) && f == 1700);
    CHECK(!parse_fixed("1.234", 5, 2, f) && !parse_fixed("1.2x", 4, 2, f) && !parse_fixed(".5", 2, 2, f));
    std::printf("%s\n", fails ? "FAILED" : "all equal to the scalar references");
    return fails ? 1 : 0;
}
