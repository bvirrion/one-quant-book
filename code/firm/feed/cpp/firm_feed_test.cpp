// Acceptance test of the Chapter 28 build, C++ side: the same sample, the same summary.
#include "firm_feed.hpp"

#include <cstdio>
#include <fstream>
#include <iostream>
#include <iterator>
#include <sstream>

using namespace firm::feed;

static std::vector<std::uint8_t> slurp(const std::string& path) {
    std::ifstream f(path, std::ios::binary);
    if (!f) throw std::runtime_error("cannot open " + path);
    return {std::istreambuf_iterator<char>(f), std::istreambuf_iterator<char>()};
}

int main() {
    const std::string dir = "code/firm/feed/data/";
    const auto data = slurp(dir + "sample.itch");
    Book book;
    std::size_t n = 0;
    decode(data, [&](const Msg& m) { book.apply(m); ++n; });

    std::ifstream e(dir + "sample.expected");
    Summary want;
    e >> want.best_bid >> want.bid_size >> want.best_ask >> want.ask_size >> want.trades >> want.shares_traded >> want.live_orders;
    const Summary got = book.summary(7);
    if (!(got == want) || book.errors() != 0 || n == 0) {
        std::cerr << "summary mismatch: bid " << got.best_bid << " x " << got.bid_size << ", ask " << got.best_ask
                  << " x " << got.ask_size << ", trades " << got.trades << ", errors " << book.errors() << "\n";
        return 1;
    }

    // a truncated buffer must throw, not guess
    bool threw = false;
    try {
        decode(std::span(data).first(data.size() - 1), [](const Msg&) {});
    } catch (const std::runtime_error&) {
        threw = true;
    }
    if (!threw) { std::cerr << "truncation not detected\n"; return 1; }

    // an unknown order reference is an error, not a crash
    Book b2;
    Msg x; x.kind = 'E'; x.ref = 42; x.shares = 100;
    b2.apply(x);
    if (b2.errors() != 1) return 1;

    std::printf("firm_feed C++: %zu messages, summary matches\n", n);
    return 0;
}
