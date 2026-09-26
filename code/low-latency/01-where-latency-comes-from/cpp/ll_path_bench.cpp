// Chapter 1 benchmark: time each stage of the toy path per message with the TSC (firm.ubench),
// over `passes` replays of Book 1's sample. Prints one CSV line per stage: stage,p50,p90,p99,p999,max (ns).
#include <cstdio>
#include <fstream>
#include <iterator>
#include <string>
#include <vector>

#include "firm_ubench.hpp"
#include "ll_path.hpp"

using namespace firm::ubench;

int main(int argc, char** argv) {
    const int passes = argc > 1 ? std::stoi(argv[1]) : 50;
    std::ifstream f("code/firm/feed/data/sample.itch", std::ios::binary);
    const std::vector<std::uint8_t> data{std::istreambuf_iterator<char>(f), std::istreambuf_iterator<char>()};
    std::vector<std::pair<std::size_t, std::size_t>> frames;
    for (std::size_t i = 0; i < data.size();) {
        const std::size_t len = (static_cast<std::size_t>(data[i]) << 8) | data[i + 1];
        frames.emplace_back(i, len + 2);
        i += len + 2;
    }
    const Clock clk = Clock::calibrate(100);
    const double ovh = clk.ns(overhead());
    std::vector<double> t[5];
    std::array<std::uint8_t, 64> buf{};
    for (int p = 0; p < passes; ++p) {
        firm::feed::Book book;
        ll::path::Decider d;
        std::uint64_t token = 0;
        for (const auto& [off, len] : frames) {
            const std::uint64_t a = tsc_start();
            const auto m = ll::path::decode_one(std::span(data).subspan(off, len));
            const std::uint64_t b = rdtscp();
            book.apply(m);
            const std::uint64_t c = rdtscp();
            const bool go = d.on(m);
            const std::uint64_t e = rdtscp();
            if (go) do_not_optimize(ll::path::encode_order(buf, ++token, 'B', 100, m.locate, m.price));
            const std::uint64_t g = rdtscp();
            if (p == 0) continue;  // first pass warms caches and the allocator
            t[0].push_back(clk.ns(b - a));
            t[1].push_back(clk.ns(c - b));
            t[2].push_back(clk.ns(e - c));
            if (go) t[3].push_back(clk.ns(g - e));
            t[4].push_back(clk.ns(g - a));
        }
    }
    const char* names[5] = {"decode", "book", "decide", "encode", "total"};
    std::printf("stage,p50,p90,p99,p999,max,n\n");
    for (int s = 0; s < 5; ++s)
        std::printf("%s,%.1f,%.1f,%.1f,%.1f,%.1f,%zu\n", names[s], quantile(t[s], 0.5), quantile(t[s], 0.9),
                    quantile(t[s], 0.99), quantile(t[s], 0.999), quantile(t[s], 1.0), t[s].size());
    std::printf("overhead,%.1f,,,,,\n", ovh);
    return 0;
}
