// firm.memkit -- memory placement tools (build of One Quant Book 13, chapter 3). Header only, C++20, Linux.
//   CachePadded<T>        a T alone on its cache line (no false sharing with its neighbours)
//   Buffer                page-aligned anonymous memory, optionally backed by transparent huge pages,
//                         pre-faulted so that the first touch on the hot path does not fault
//   chase_ring / chase    a pointer-chase probe: one dependent load per step through a cyclic permutation
#pragma once
#include <sys/mman.h>

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <new>
#include <random>
#include <stdexcept>
#include <utility>
#include <vector>

namespace firm::memkit {

inline constexpr std::size_t kLine = 64;  // x86-64 cache line (std::hardware_destructive_interference_size)

template <class T>
struct alignas(kLine) CachePadded {
    T value{};
    char pad[kLine - (sizeof(T) % kLine == 0 ? kLine : sizeof(T) % kLine)];
};

class Buffer {
public:
    Buffer(std::size_t bytes, bool huge) : size_(round_up(bytes, huge ? (2u << 20) : 4096u)) {
        void* p = mmap(nullptr, size_, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
        if (p == MAP_FAILED) throw std::bad_alloc();
        data_ = static_cast<std::uint8_t*>(p);
        huge_ = huge && madvise(data_, size_, MADV_HUGEPAGE) == 0;
        if (!huge) madvise(data_, size_, MADV_NOHUGEPAGE);
        std::memset(data_, 0, size_);  // pre-fault every page now, not on the hot path
    }
    Buffer(const Buffer&) = delete;
    Buffer& operator=(const Buffer&) = delete;
    ~Buffer() { munmap(data_, size_); }
    std::uint8_t* data() const { return data_; }
    std::size_t size() const { return size_; }
    bool huge_requested() const { return huge_; }

private:
    static std::size_t round_up(std::size_t n, std::size_t a) { return (n + a - 1) / a * a; }
    std::uint8_t* data_ = nullptr;
    std::size_t size_;
    bool huge_ = false;
};

// Lay out `n` slots of `stride` bytes as one random cycle: slot i holds the address of the next slot.
// With random=false the cycle visits the slots in address order (what a prefetcher can follow).
inline void chase_ring(std::uint8_t* base, std::size_t n, std::size_t stride, bool random, std::uint64_t seed = 1) {
    std::vector<std::size_t> order(n);
    for (std::size_t i = 0; i < n; ++i) order[i] = i;
    if (random) {
        std::mt19937_64 rng(seed);
        for (std::size_t i = n - 1; i > 0; --i) std::swap(order[i], order[rng() % (i + 1)]);  // Fisher-Yates
    }
    for (std::size_t i = 0; i < n; ++i) {
        void* next = base + order[(i + 1) % n] * stride;
        std::memcpy(base + order[i] * stride, &next, sizeof next);
    }
}

// Follow the ring for `steps` loads; each load's address is the previous load's value.
inline const void* chase(const void* start, std::size_t steps) {
    const void* p = start;
    for (std::size_t i = 0; i < steps; ++i) p = *static_cast<const void* const*>(p);
    return p;
}

}  // namespace firm::memkit
