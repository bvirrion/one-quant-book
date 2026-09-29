// Book 18, chapter 25: a single-producer single-consumer queue (bounded, lock-free) in C++20.
#pragma once
#include <array>
#include <atomic>
#include <cstddef>
#include <optional>

namespace iv {

template <typename T, std::size_t N>
    requires(N > 1 && (N & (N - 1)) == 0)
class SpscQueue {
public:
    bool push(const T& v) {  // producer thread only
        const std::size_t t = tail_.load(std::memory_order_relaxed);
        if (t - head_.load(std::memory_order_acquire) == N) return false;  // full
        buf_[t & (N - 1)] = v;
        tail_.store(t + 1, std::memory_order_release);  // publishes the element
        return true;
    }
    std::optional<T> pop() {  // consumer thread only
        const std::size_t h = head_.load(std::memory_order_relaxed);
        if (h == tail_.load(std::memory_order_acquire)) return std::nullopt;  // empty
        T v = buf_[h & (N - 1)];
        head_.store(h + 1, std::memory_order_release);  // frees the slot
        return v;
    }

private:
    std::array<T, N> buf_{};
    alignas(64) std::atomic<std::size_t> head_{0};  // written by the consumer
    alignas(64) std::atomic<std::size_t> tail_{0};  // written by the producer, on its own cache line
};

}  // namespace iv
