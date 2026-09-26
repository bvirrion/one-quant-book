// Chapter 2: the kernels compute what they claim (timings are the benchmark's business).
#include "ll_cpu.hpp"

#include <algorithm>
#include <cstdio>
#include <random>
#include <vector>

using namespace ll::cpu;

int main() {
    std::mt19937 rng(7);
    std::vector<int> d(32768);
    for (auto& v : d) v = static_cast<int>(rng() % 256);
    std::int64_t want = 0;
    for (int v : d) if (v >= 128) want += v;
    if (sum_branchy(d.data(), d.size()) != want || sum_branchless(d.data(), d.size()) != want) return 1;
    std::sort(d.begin(), d.end());
    if (sum_branchy(d.data(), d.size()) != want) return 1;
    std::vector<double> x(1003);
    for (std::size_t i = 0; i < x.size(); ++i) x[i] = static_cast<double>(i % 7);  // exact in binary
    const double s = sum_chains<1>(x.data(), x.size());
    if (sum_chains<4>(x.data(), x.size()) != s || sum_chains<8>(x.data(), x.size()) != s) return 1;
    if (add_chain_reg(100) != 10 * 4950 || add_chain_imm(100) != 1000) return 1;
    std::puts("cpu kernels ok");
    return 0;
}
