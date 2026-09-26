// Chapter 19 benchmark: time per event of three book builders on an event file (48-byte records).
// Usage: ll_books_bench <events.bin> <tick> [ladder width]; with a width, only the ladder runs (and its total time). Each event is timed with the TSC (the timer's own median cost, measured
// first, is subtracted); each structure runs the file twice and the second pass is reported, as quantiles.
// Output: structure,q50,q90,q99,q999 (ns), then recentrings of the ladder.
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iterator>
#include <string>

#include "firm_ubench.hpp"
#include "ll_books.hpp"

using namespace firm::ubench;

static std::vector<firm::feed2::Event> events(const char* path) {
    std::ifstream f(path, std::ios::binary);
    const std::vector<std::uint8_t> b{std::istreambuf_iterator<char>(f), {}};
    std::vector<firm::feed2::Event> out;
    for (std::size_t i = 0; i + 48 <= b.size(); i += 48) {
        firm::feed2::Event e;
        e.kind = b[i];
        e.side = b[i + 1];
        std::memcpy(&e.ref, &b[i + 20], 8);
        std::memcpy(&e.ref2, &b[i + 28], 8);
        std::memcpy(&e.price, &b[i + 36], 4);
        std::memcpy(&e.qty, &b[i + 40], 8);
        out.push_back(e);
    }
    return out;
}

template <class Book>
static void measure(const char* name, const std::vector<firm::feed2::Event>& ev, const Clock& clk, double ovh,
                    Book make()) {
    std::vector<double> t(ev.size());
    for (int pass = 0; pass < 2; ++pass) {
        Book b = make();
        for (std::size_t i = 0; i < ev.size(); ++i) {
            const std::uint64_t a = tsc_start();
            b.apply(ev[i]);
            t[i] = clk.ns(rdtscp() - a) - ovh;
        }
        clobber();
    }
    std::printf("%s,%.1f,%.1f,%.1f,%.1f\n", name, quantile(t, 0.5), quantile(t, 0.9), quantile(t, 0.99), quantile(t, 0.999));
}

int main(int argc, char** argv) {
    if (argc < 3) return 1;
    const Clock clk = Clock::calibrate();
    const double ovh = clk.ns(overhead());
    const auto ev = events(argv[1]);
    const auto tick = static_cast<std::uint32_t>(std::atoi(argv[2]));
    std::printf("structure,q50,q90,q99,q999\n");
    static std::uint32_t g_tick;
    static std::size_t g_width;
    g_tick = tick;
    g_width = argc > 3 ? static_cast<std::size_t>(std::atol(argv[3])) : 4096;
    if (argc <= 3) {
        measure<ll::books::TreeBook>("tree", ev, clk, ovh, [] { return ll::books::TreeBook(); });
        measure<ll::books::VecBook>("vector", ev, clk, ovh, [] { return ll::books::VecBook(); });
    }
    measure<firm::book::LadderBook>("ladder", ev, clk, ovh, [] { return firm::book::LadderBook(g_tick, g_width, 1 << 17); });
    firm::book::LadderBook b(tick, g_width, 1 << 17);
    const double w0 = raw_ns();
    for (const auto& e : ev) b.apply(e);
    std::printf("total_ms,%.3f\n", (raw_ns() - w0) / 1e6);
    std::printf("recentrings,%llu\nevents,%zu\ntimer_ns,%.1f\n", static_cast<unsigned long long>(b.recentrings), ev.size(), ovh);
    return 0;
}
