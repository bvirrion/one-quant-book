// Chapter 11 of One Quant Book 13: a lock-free stack, four shared counters, and a litmus test of memory ordering.
#pragma once
#include <atomic>
#include <cstdint>
#include <mutex>
#include <thread>
#include <vector>

#include "../../../firm/memkit/cpp/firm_memkit.hpp"

namespace ll::lf {

// Treiber stack over a fixed pool of nodes. The head packs a 32-bit tag with a 32-bit node index (0 = empty); every
// successful update increments the tag, so a head that was popped and pushed back (A -> B -> A) no longer compares
// equal: the ABA problem cannot fool the compare-and-swap. Nodes are never freed, so no reclamation is needed.
class Stack {
public:
    explicit Stack(std::uint32_t capacity) : next_(capacity + 1) {}

    void push(std::uint32_t node) {  // node in 1..capacity
        std::uint64_t old = head_.load(std::memory_order_relaxed);
        for (;;) {
            next_[node].store(static_cast<std::uint32_t>(old), std::memory_order_relaxed);
            const std::uint64_t desired = ((old >> 32) + 1) << 32 | node;
            if (head_.compare_exchange_weak(old, desired, std::memory_order_release, std::memory_order_relaxed)) return;
        }
    }

    std::uint32_t pop() {  // 0 when empty
        std::uint64_t old = head_.load(std::memory_order_acquire);
        for (;;) {
            const auto node = static_cast<std::uint32_t>(old);
            if (node == 0) return 0;
            const std::uint32_t next = next_[node].load(std::memory_order_relaxed);
            const std::uint64_t desired = ((old >> 32) + 1) << 32 | next;
            if (head_.compare_exchange_weak(old, desired, std::memory_order_acquire, std::memory_order_acquire)) return node;
        }
    }

private:
    std::atomic<std::uint64_t> head_{0};
    std::vector<std::atomic<std::uint32_t>> next_;
};

// The same stack without the tag, for exercise 7: correct only as long as no ABA interleaving happens.
class UntaggedStack {
public:
    explicit UntaggedStack(std::uint32_t capacity) : next_(capacity + 1) {}
    void push(std::uint32_t node) {
        std::uint32_t old = head_.load(std::memory_order_relaxed);
        do next_[node].store(old, std::memory_order_relaxed);
        while (!head_.compare_exchange_weak(old, node, std::memory_order_release, std::memory_order_relaxed));
    }
    std::uint32_t pop() {
        std::uint32_t old = head_.load(std::memory_order_acquire);
        while (old != 0 && !head_.compare_exchange_weak(old, next_[old].load(std::memory_order_relaxed), std::memory_order_acquire)) {
        }
        return old;
    }

private:
    std::atomic<std::uint32_t> head_{0};
    std::vector<std::atomic<std::uint32_t>> next_;
};

// Four ways for threads to count events. Each returns the final total after `threads` threads add `per` each.
inline std::uint64_t count_mutex(int threads, std::uint64_t per) {
    std::mutex m;
    std::uint64_t total = 0;
    std::vector<std::thread> ts;
    for (int t = 0; t < threads; ++t) ts.emplace_back([&] { for (std::uint64_t i = 0; i < per; ++i) { std::lock_guard g(m); ++total; } });
    for (auto& t : ts) t.join();
    return total;
}

inline std::uint64_t count_cas(int threads, std::uint64_t per) {
    std::atomic<std::uint64_t> total{0};
    std::vector<std::thread> ts;
    for (int t = 0; t < threads; ++t)
        ts.emplace_back([&] {
            for (std::uint64_t i = 0; i < per; ++i) {
                std::uint64_t v = total.load(std::memory_order_relaxed);
                while (!total.compare_exchange_weak(v, v + 1, std::memory_order_relaxed)) {
                }
            }
        });
    for (auto& t : ts) t.join();
    return total.load();
}

inline std::uint64_t count_fetch_add(int threads, std::uint64_t per) {
    std::atomic<std::uint64_t> total{0};
    std::vector<std::thread> ts;
    for (int t = 0; t < threads; ++t) ts.emplace_back([&] { for (std::uint64_t i = 0; i < per; ++i) total.fetch_add(1, std::memory_order_relaxed); });
    for (auto& t : ts) t.join();
    return total.load();
}

inline std::uint64_t count_per_thread(int threads, std::uint64_t per) {
    std::vector<firm::memkit::CachePadded<std::atomic<std::uint64_t>>> c(static_cast<std::size_t>(threads));
    std::vector<std::thread> ts;
    for (int t = 0; t < threads; ++t)
        ts.emplace_back([&, t] { for (std::uint64_t i = 0; i < per; ++i) c[static_cast<std::size_t>(t)].value.fetch_add(1, std::memory_order_relaxed); });
    for (auto& t : ts) t.join();
    std::uint64_t total = 0;
    for (auto& x : c) total += x.value.load();
    return total;
}

// Store-buffer litmus test: thread A does x = 1; r1 = y. Thread B does y = 1; r2 = x. Under sequential consistency at
// least one of r1, r2 is 1. Returns how many of `trials` rounds ended with r1 == r2 == 0.
template <std::memory_order Store, std::memory_order Load>
std::uint64_t store_buffer_zeros(std::uint64_t trials) {
    firm::memkit::CachePadded<std::atomic<int>> x, y;
    firm::memkit::CachePadded<std::atomic<std::uint64_t>> go_a, go_b, done;
    std::atomic<int> r1{0}, r2{0};
    std::uint64_t zeros = 0;
    std::thread b([&] {
        for (std::uint64_t k = 1; k <= trials; ++k) {
            while (go_b.value.load(std::memory_order_acquire) != k) {
            }
            y.value.store(1, Store);
            r2.store(x.value.load(Load), std::memory_order_relaxed);
            done.value.fetch_add(1, std::memory_order_acq_rel);
        }
    });
    for (std::uint64_t k = 1; k <= trials; ++k) {
        x.value.store(0, std::memory_order_relaxed);
        y.value.store(0, std::memory_order_relaxed);
        std::atomic_thread_fence(std::memory_order_seq_cst);
        const std::uint64_t target = done.value.load(std::memory_order_acquire) + 1;
        go_b.value.store(k, std::memory_order_release);
        x.value.store(1, Store);
        r1.store(y.value.load(Load), std::memory_order_relaxed);
        while (done.value.load(std::memory_order_acquire) != target) {
        }
        zeros += r1.load(std::memory_order_relaxed) == 0 && r2.load(std::memory_order_relaxed) == 0;
    }
    b.join();
    return zeros;
}

}  // namespace ll::lf
