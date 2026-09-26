// Chapter 24: how fast a backup catches up. Builds a journal of 2 million entries (a random walk of prices, with the
// acknowledgement and the fill of every order the replica sends), then times one replica applying all of it; prints
// the entries, the seconds and the nanoseconds per entry (best of five).
#include <chrono>
#include <cstdio>
#include <random>
#include <vector>

#include "firm_sequencer.hpp"

using namespace firm::seq;

int main() {
    std::mt19937_64 rng(7);
    Journal j;
    Replica live;
    std::int64_t p = 1'000'000;
    while (j.entries().size() < 2'000'000) {
        p += 100 * static_cast<std::int64_t>(rng() % 5) - 200;
        auto add = [&](Entry e) {
            j.append(e);
            return live.apply(j.entries().back());
        };
        for (const auto& o : add(Entry{1, 0, 'M', p})) {
            add(Entry{1, 0, 'Q', o.cl});
            add(Entry{1, 0, 'E', o.cl, o.qty, 0});
        }
    }
    double best = 1e9;
    std::uint64_t h = 0;
    for (int pass = 0; pass < 5; ++pass) {
        Replica r;
        const auto t0 = std::chrono::steady_clock::now();
        for (const Entry& e : j.entries()) r.apply(e);
        const double s = std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count();
        best = std::min(best, s);
        h = r.hash;
    }
    if (h != live.hash) std::printf("error,replay differs\n");
    std::printf("apply,%zu,%.4f,%.1f\n", j.entries().size(), best, best * 1e9 / static_cast<double>(j.entries().size()));
    return 0;
}
