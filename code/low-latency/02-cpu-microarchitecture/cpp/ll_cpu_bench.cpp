// Chapter 2 benchmark. Modes:
//   branch  -> variant,order,ns_per_element   (sorted and shuffled data, branchy and branchless)
//   chains  -> accumulators,ns_per_add
//   freq    -> ghz_reg,adds_per_cycle_imm     (clock from a register add chain; renamer folding)
//   blocks  -> block,ns_per_element           (values alternate above and below 128 in blocks of b)
#include <algorithm>
#include <chrono>
#include <cstdio>
#include <cstring>
#include <random>
#include <vector>

#include "firm_ubench.hpp"
#include "ll_cpu.hpp"

using namespace ll::cpu;
using sc = std::chrono::steady_clock;

template <class F>
double best_ns(F&& f, int reps) {
    double best = 1e300;
    for (int r = 0; r < reps; ++r) {
        const auto t0 = sc::now();
        f();
        best = std::min(best, std::chrono::duration<double, std::nano>(sc::now() - t0).count());
    }
    return best;
}

int main(int argc, char** argv) {
    const char* mode = argc > 1 ? argv[1] : "branch";
    if (!std::strcmp(mode, "branch")) {
        std::mt19937 rng(1);
        std::vector<int> d(32768);
        for (auto& v : d) v = static_cast<int>(rng() % 256);
        std::vector<int> sorted = d;
        std::sort(sorted.begin(), sorted.end());
        std::printf("variant,order,ns_per_element\n");
        for (int v = 0; v < 2; ++v)
            for (int o = 0; o < 2; ++o) {
                const auto& a = o ? d : sorted;
                const double ns = best_ns([&] {
                    for (int k = 0; k < 20; ++k)
                        firm::ubench::do_not_optimize(v ? sum_branchless(a.data(), a.size()) : sum_branchy(a.data(), a.size()));
                }, 30);
                std::printf("%s,%s,%.4f\n", v ? "branchless" : "branchy", o ? "shuffled" : "sorted", ns / (20.0 * 32768));
            }
    } else if (!std::strcmp(mode, "chains")) {
        std::vector<double> x(4096, 1.0);  // 32 KiB: stays in the first-level cache
        std::printf("accumulators,ns_per_add\n");
        auto one = [&](auto f, int k) {
            const double ns = best_ns([&] { for (int r = 0; r < 100; ++r) firm::ubench::do_not_optimize(f(x.data(), x.size())); }, 30);
            std::printf("%d,%.4f\n", k, ns / (100.0 * 4096));
        };
        one(sum_chains<1>, 1); one(sum_chains<2>, 2); one(sum_chains<4>, 4); one(sum_chains<8>, 8); one(sum_chains<16>, 16);
    } else if (!std::strcmp(mode, "blocks")) {
        std::mt19937 rng(3);
        std::printf("block,ns_per_element\n");
        for (int b : {1, 2, 4, 8, 16, 64, 1024}) {
            std::vector<int> d(32768);
            for (std::size_t i = 0; i < d.size(); ++i)
                d[i] = static_cast<int>((i / static_cast<std::size_t>(b)) % 2 ? 128 + rng() % 128 : rng() % 128);
            const double ns = best_ns([&] {
                for (int k = 0; k < 20; ++k) firm::ubench::do_not_optimize(sum_branchy(d.data(), d.size()));
            }, 30);
            std::printf("%d,%.4f\n", b, ns / (20.0 * 32768));
        }
    } else {
        const std::uint64_t n = 5'000'000;
        const double reg = best_ns([&] { firm::ubench::do_not_optimize(add_chain_reg(n)); }, 15);
        const double imm = best_ns([&] { firm::ubench::do_not_optimize(add_chain_imm(n)); }, 15);
        const double ghz = 10.0 * static_cast<double>(n) / reg;
        std::printf("ghz_reg,adds_per_cycle_imm\n%.3f,%.3f\n", ghz, (10.0 * static_cast<double>(n) / imm) / ghz);
    }
    return 0;
}
