#pragma once
#include <atomic>
#include <cstddef>
#include <cstdint>

template <std::size_t N>
struct ShmRing {                                // lives in shared memory; N is a power of two
    static_assert(std::atomic<std::uint64_t>::is_always_lock_free);
    alignas(64) std::atomic<std::uint64_t> head{0};   // the next slot to write, producer only
    alignas(64) std::atomic<std::uint64_t> tail{0};   // the next slot to read, consumer only
    alignas(64) std::uint64_t slots[N];

    bool push(std::uint64_t v) {
        std::uint64_t h = head.load(std::memory_order_relaxed);
        if (h - tail.load(std::memory_order_acquire) == N) return false;
        slots[h & (N - 1)] = v;
        head.store(h + 1, std::memory_order_release);   // publish only a complete slot
        return true;
    }
    bool pop(std::uint64_t& v) {
        std::uint64_t t = tail.load(std::memory_order_relaxed);
        if (t == head.load(std::memory_order_acquire)) return false;
        v = slots[t & (N - 1)];
        tail.store(t + 1, std::memory_order_release);
        return true;
    }
};
