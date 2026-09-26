// Chapter 14 benchmark.
//   scan     ns per call to find a delimiter placed at the end of a message of L bytes: scalar, SSE2, AVX2
//   split    ns per FIX-like message to find every SOH: scalar, AVX2
//   parse    ns per eight-digit field: scalar loop, SWAR, SSE4.1, std::from_chars; and per decimal price
//   reval    ns per option to revalue a book stored as records or as columns (built at several flag sets)
#include <charconv>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

#include "firm_simdscan.hpp"
#include "firm_ubench.hpp"
#include "ll_simd.hpp"

using namespace firm::simdscan;
using namespace firm::ubench;

// Median over `samples` of the time of `batch` calls, divided by batch.
template <class F>
static double per_call(const Clock& clk, F&& f, int batch = 1000, int samples = 301) {
    std::vector<double> t;
    for (int s = 0; s < samples + 10; ++s) {
        const std::uint64_t a = tsc_start();
        for (int i = 0; i < batch; ++i) f(i);
        const std::uint64_t b = rdtscp();
        if (s >= 10) t.push_back(clk.ns(b - a) / batch);
    }
    return quantile(t, 0.5);
}

static void scan(const Clock& clk) {
    std::printf("bytes,scalar,sse2,avx2\n");
    for (const std::size_t L : {8, 16, 24, 32, 48, 64, 96, 128, 192, 256, 512, 1024, 4096}) {
        std::vector<char> m(L, 'x');
        m[L - 1] = '\x01';
        const char* p = m.data();
        std::size_t sink = 0;
        const double s = per_call(clk, [&](int) { do_not_optimize(p); sink += find_byte_scalar(p, L, '\x01'); });
        const double e = per_call(clk, [&](int) { do_not_optimize(p); sink += find_byte_sse2(p, L, '\x01'); });
        const double v = per_call(clk, [&](int) { do_not_optimize(p); sink += find_byte_avx2(p, L, '\x01'); });
        do_not_optimize(sink);
        std::printf("%zu,%.3f,%.3f,%.3f\n", L, s, e, v);
    }
}

static std::vector<std::string> fix_messages() {
    std::vector<std::string> out;
    for (int i = 0; i < 64; ++i) {
        std::string s = "8=FIX.4.4\x01" "9=178\x01" "35=D\x01" "34=" + std::to_string(1000 + i) + "\x01" +
                        "49=FIRM\x01" "56=EXCH\x01" "52=20260925-14:30:00.123456\x01" "11=ORD" + std::to_string(77000 + i) +
                        "\x01" "55=ESZ6\x01" "54=1\x01" "38=" + std::to_string(1 + i % 9) + "\x01" "40=2\x01" "44=5723." +
                        std::to_string(25 + i % 50) + "\x01" "59=0\x01" "60=20260925-14:30:00.123400\x01" "10=123\x01";
        out.push_back(s);
    }
    return out;
}

static void split(const Clock& clk) {
    const auto msgs = fix_messages();
    std::uint32_t pos[64];
    std::size_t sink = 0, bytes = 0;
    for (const auto& m : msgs) bytes += m.size();
    const double s = per_call(clk, [&](int i) {
        const auto& m = msgs[static_cast<std::size_t>(i) & 63];
        sink += positions_scalar(m.data(), m.size(), '\x01', pos, 64);
        do_not_optimize(pos);
    });
    const double v = per_call(clk, [&](int i) {
        const auto& m = msgs[static_cast<std::size_t>(i) & 63];
        sink += positions_avx2(m.data(), m.size(), '\x01', pos, 64);
        do_not_optimize(pos);
    });
    do_not_optimize(sink);
    std::printf("method,ns_per_message,mean_bytes,fields\nscalar,%.2f,%.1f,%zu\navx2,%.2f,%.1f,%zu\n", s,
                static_cast<double>(bytes) / 64, positions_scalar(msgs[0].data(), msgs[0].size(), '\x01', pos, 64), v,
                static_cast<double>(bytes) / 64, positions_scalar(msgs[0].data(), msgs[0].size(), '\x01', pos, 64));
}

static void parse(const Clock& clk) {
    std::vector<std::string> digits, prices;
    std::uint64_t x = 12345;
    for (int i = 0; i < 1024; ++i) {
        x = x * 6364136223846793005ULL + 1442695040888963407ULL;
        char b[32];
        std::snprintf(b, sizeof b, "%08u", static_cast<unsigned>((x >> 33) % 100000000));
        digits.emplace_back(b);
        std::snprintf(b, sizeof b, "%u.%04u", static_cast<unsigned>((x >> 20) % 10000), static_cast<unsigned>((x >> 40) % 10000));
        prices.emplace_back(b);
    }
    std::uint64_t sink = 0;
    auto d = [&](int i) { return digits[static_cast<std::size_t>(i) & 1023].data(); };
    const double a = per_call(clk, [&](int i) { sink += parse8_scalar(d(i)); });
    const double b = per_call(clk, [&](int i) { sink += parse8_swar(d(i)); });
    const double c = per_call(clk, [&](int i) { sink += parse8_sse(d(i)); });
    const double e = per_call(clk, [&](int i) {
        std::uint32_t v = 0;
        std::from_chars(d(i), d(i) + 8, v);
        sink += v;
    });
    const double f = per_call(clk, [&](int i) {
        const std::string& p = prices[static_cast<std::size_t>(i) & 1023];
        std::int64_t v = 0;
        parse_fixed(p.data(), p.size(), 4, v);
        sink += static_cast<std::uint64_t>(v);
    });
    const double g = per_call(clk, [&](int i) {
        const std::string& p = prices[static_cast<std::size_t>(i) & 1023];
        sink += static_cast<std::uint64_t>(std::strtod(p.c_str(), nullptr) * 10000.0 + 0.5);
    });
    do_not_optimize(sink);
    std::printf("method,ns\nscalar loop,%.3f\nSWAR,%.3f\nSSE4.1,%.3f\nfrom_chars,%.3f\nparse_fixed,%.3f\nstrtod,%.3f\n", a, b,
                c, e, f, g);
}

static void reval(const Clock& clk) {
    std::printf("options,rows,columns\n");
    for (const std::size_t n : {std::size_t{1024}, std::size_t{1} << 20}) {
        std::vector<ll::simd::OptionRow> rows;
        ll::simd::OptionColumns cols;
        ll::simd::make_book(n, rows, cols);
        std::vector<double> out(n);
        const ll::simd::Move m{1.25, 0.4, -1.0 / 365};
        const int batch = n > 100000 ? 1 : 100;
        const int samples = n > 100000 ? 31 : 301;
        const double r = per_call(clk, [&](int) { ll::simd::revalue_rows(rows.data(), n, m, out.data()); clobber(); },
                                  batch, samples);
        const double c = per_call(clk, [&](int) { ll::simd::revalue_columns(cols, m, out.data()); clobber(); }, batch,
                                  samples);
        std::printf("%zu,%.4f,%.4f\n", n, r / static_cast<double>(n), c / static_cast<double>(n));
    }
}

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    const std::string mode = argv[1];
    const Clock clk = Clock::calibrate();
    if (mode == "scan") scan(clk);
    else if (mode == "split") split(clk);
    else if (mode == "parse") parse(clk);
    else if (mode == "reval") reval(clk);
    else return 1;
    return 0;
}
