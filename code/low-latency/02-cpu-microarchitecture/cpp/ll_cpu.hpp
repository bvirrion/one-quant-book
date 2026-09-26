// Chapter 2 of One Quant Book 13: kernels that expose the pipeline, the branch predictor and the
// out-of-order engine. Each kernel is small enough to read in the disassembly.
#pragma once
#include <cstddef>
#include <cstdint>

namespace ll::cpu {

// The loop of the 2012 question: add the elements >= 128. The asm statement is empty but opaque,
// so the compiler cannot turn the branch into a conditional move.
inline std::int64_t sum_branchy(const int* d, std::size_t n) {
    std::int64_t s = 0;
    for (std::size_t i = 0; i < n; ++i) {
        if (d[i] >= 128) {
            s += d[i];
            asm volatile("" : "+r"(s));
        }
    }
    return s;
}

// The same sum without a data-dependent branch: a mask of all ones or all zeros.
inline std::int64_t sum_branchless(const int* d, std::size_t n) {
    std::int64_t s = 0;
    for (std::size_t i = 0; i < n; ++i) {
        const std::int64_t mask = -static_cast<std::int64_t>(d[i] >= 128);
        s += d[i] & mask;
        asm volatile("" : "+r"(s));
    }
    return s;
}

// A sum with K independent accumulators: one chain is bound by the latency of an addition,
// K chains by the adders' throughput. No -ffast-math: the order of additions is fixed by the code.
template <int K>
double sum_chains(const double* x, std::size_t n) {
    double acc[K] = {};
    std::size_t i = 0;
    for (; i + K <= n; i += K) {
#pragma GCC unroll 16
        for (int k = 0; k < K; ++k) acc[k] += x[i + static_cast<std::size_t>(k)];
    }
    double s = 0.0;
    for (int k = 0; k < K; ++k) s += acc[k];
    for (; i < n; ++i) s += x[i];
    return s;
}

// n iterations of ten dependent register additions: ten cycles an iteration on any core, so the
// time it takes measures the core's clock.
inline std::uint64_t add_chain_reg(std::uint64_t n) {
    std::uint64_t x = 0;
    for (std::uint64_t i = 0; i < n; ++i)
        asm volatile(
            "add %1, %0\n\tadd %1, %0\n\tadd %1, %0\n\tadd %1, %0\n\tadd %1, %0\n\t"
            "add %1, %0\n\tadd %1, %0\n\tadd %1, %0\n\tadd %1, %0\n\tadd %1, %0"
            : "+r"(x)
            : "r"(i));
    return x;
}

// The same chain with a small immediate: recent cores can resolve these in the renamer, several
// per cycle, so the "dependency chain" is not one.
inline std::uint64_t add_chain_imm(std::uint64_t n) {
    std::uint64_t x = 0;
    for (std::uint64_t i = 0; i < n; ++i)
        asm volatile(
            "add $1, %0\n\tadd $1, %0\n\tadd $1, %0\n\tadd $1, %0\n\tadd $1, %0\n\t"
            "add $1, %0\n\tadd $1, %0\n\tadd $1, %0\n\tadd $1, %0\n\tadd $1, %0"
            : "+r"(x));
    return x;
}

}  // namespace ll::cpu
