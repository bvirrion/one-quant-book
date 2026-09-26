// Chapter 9 benchmark, C++ side of the Rust comparison: the same decode of Book 1's sample and the same three
// summations as rust/src/bin/ll_rust_bench.rs. Prints impl,ns.
#include <algorithm>
#include <chrono>
#include <cstdio>
#include <fstream>
#include <iterator>
#include <vector>

#include "../../../firm/feed/cpp/firm_feed.hpp"
#include "firm_ubench.hpp"

template <class F>
double best(F&& f, int reps) {
    double b = 1e300;
    for (int r = 0; r < reps; ++r) {
        const auto t0 = std::chrono::steady_clock::now();
        f();
        b = std::min(b, std::chrono::duration<double, std::nano>(std::chrono::steady_clock::now() - t0).count());
    }
    return b;
}

int main() {
    std::ifstream f("code/firm/feed/data/sample.itch", std::ios::binary);
    const std::vector<std::uint8_t> data{std::istreambuf_iterator<char>(f), std::istreambuf_iterator<char>()};
    std::size_t n_msgs = 0;
    firm::feed::decode(data, [&](const firm::feed::Msg&) { ++n_msgs; });
    const int passes = 300;
    const double dec = best([&] {
        std::uint64_t acc = 0;
        for (int p = 0; p < passes; ++p) firm::feed::decode(data, [&](const firm::feed::Msg& m) { acc = (acc ^ m.ref) * 1099511628211ull; });
        firm::ubench::do_not_optimize(acc);
    }, 5) / (passes * static_cast<double>(n_msgs));
    std::vector<std::uint32_t> v(1u << 16);
    for (std::size_t i = 0; i < v.size(); ++i) v[i] = static_cast<std::uint32_t>(i);
    std::vector<std::size_t> idx(v.size());
    for (std::size_t i = 0; i < idx.size(); ++i) idx[i] = (i * 7919) % v.size();
    const double n = static_cast<double>(v.size());
    const double counted = best([&] { std::uint64_t s = 0; for (std::size_t i = 0; i < v.size(); ++i) s += v[i]; firm::ubench::do_not_optimize(s); }, 50) / n;
    const double checked = best([&] { std::uint64_t s = 0; for (auto i : idx) s += v.at(i); firm::ubench::do_not_optimize(s); }, 50) / n;
    const double unchecked = best([&] { std::uint64_t s = 0; for (auto i : idx) s += v[i]; firm::ubench::do_not_optimize(s); }, 50) / n;
    std::printf("impl,ns\nC++ decode,%.3f\nC++ counted loop,%.4f\nC++ gather checked,%.4f\nC++ gather unchecked,%.4f\n", dec, counted, checked, unchecked);
    return 0;
}
