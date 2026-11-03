#include <atomic>
#include <cstddef>
#include <cstdio>
#include <thread>
#include <vector>

template <std::size_t N>  // N is a power of two
class Mpmc {
    struct Slot {
        std::atomic<std::size_t> seq;
        long value;
    };
    alignas(64) std::atomic<std::size_t> tail_{0};
    alignas(64) std::atomic<std::size_t> head_{0};
    alignas(64) Slot slots_[N];

public:
    Mpmc() {
        for (std::size_t i = 0; i < N; ++i)
            slots_[i].seq.store(i, std::memory_order_relaxed);
    }
    bool try_push(long v) {
        std::size_t pos = tail_.load(std::memory_order_relaxed);
        for (;;) {
            Slot& s = slots_[pos & (N - 1)];
            std::size_t seq = s.seq.load(std::memory_order_acquire);
            if (seq == pos) {
                if (tail_.compare_exchange_weak(pos, pos + 1,
                                                std::memory_order_relaxed)) {
                    s.value = v;
                    s.seq.store(pos + 1, std::memory_order_release);
                    return true;
                }
            } else if (seq < pos) {
                return false;  // full
            } else {
                pos = tail_.load(std::memory_order_relaxed);
            }
        }
    }
    bool try_pop(long& out) {
        std::size_t pos = head_.load(std::memory_order_relaxed);
        for (;;) {
            Slot& s = slots_[pos & (N - 1)];
            std::size_t seq = s.seq.load(std::memory_order_acquire);
            if (seq == pos + 1) {
                if (head_.compare_exchange_weak(pos, pos + 1,
                                                std::memory_order_relaxed)) {
                    out = s.value;
                    s.seq.store(pos + N, std::memory_order_release);
                    return true;
                }
            } else if (seq < pos + 1) {
                return false;  // empty
            } else {
                pos = head_.load(std::memory_order_relaxed);
            }
        }
    }
    // Test hooks: the two halves of try_push, so a schedule can stop a producer between them.
    std::size_t claim() { return tail_.fetch_add(1, std::memory_order_relaxed); }
    void commit(std::size_t pos, long v) {
        slots_[pos & (N - 1)].value = v;
        slots_[pos & (N - 1)].seq.store(pos + 1, std::memory_order_release);
    }
};

Mpmc<8> q;
Mpmc<8> replay;

int main() {
    std::size_t stalled = replay.claim();  // producer 1 claims position 0 and is suspended
    int later = 0;
    for (long v = 100; replay.try_push(v); ++v) ++later;  // producer 2 pushes as much as it can
    long v = -1;
    bool got = replay.try_pop(v);
    std::printf("later pushes %d, pop while stalled %d\n", later, got);
    replay.commit(stalled, 7);
    got = replay.try_pop(v);
    std::printf("pop after resume %d value %ld\n", got, v);

    std::atomic<long> sum{0};
    const long each = 50000;
    std::vector<std::thread> pool;
    for (int t = 0; t < 2; ++t) {
        pool.emplace_back([&] {
            for (long i = 1; i <= each; ++i)
                while (!q.try_push(i)) {
                }
        });
        pool.emplace_back([&] {
            long x;
            for (long i = 1; i <= each; ++i) {
                while (!q.try_pop(x)) {
                }
                sum.fetch_add(x, std::memory_order_relaxed);
            }
        });
    }
    for (auto& th : pool) th.join();
    std::printf("sum %ld expected %ld\n", sum.load(), 2 * each * (each + 1) / 2);
}
