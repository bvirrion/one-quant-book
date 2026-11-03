#include <cstdlib>
#include <atomic>
#include <chrono>
#include <cstddef>
#include <cstdio>
#include <memory>
#include <thread>

constexpr std::size_t N = 1024;

struct Adjacent {
    std::atomic<std::size_t> head{0}, tail{0};
    long slots[N];

    bool push(long v) {
        const std::size_t t = tail.load(std::memory_order_relaxed);
        if (t - head.load(std::memory_order_acquire) == N) return false;
        slots[t & (N - 1)] = v;
        tail.store(t + 1, std::memory_order_release);
        return true;
    }
    bool pop(long& out) {
        const std::size_t h = head.load(std::memory_order_relaxed);
        if (h == tail.load(std::memory_order_acquire)) return false;
        out = slots[h & (N - 1)];
        head.store(h + 1, std::memory_order_release);
        return true;
    }
};

struct Padded {
    alignas(64) std::atomic<std::size_t> head{0};
    alignas(64) std::atomic<std::size_t> tail{0};
    alignas(64) long slots[N];

    bool push(long v) {
        const std::size_t t = tail.load(std::memory_order_relaxed);
        if (t - head.load(std::memory_order_acquire) == N) return false;
        slots[t & (N - 1)] = v;
        tail.store(t + 1, std::memory_order_release);
        return true;
    }
    bool pop(long& out) {
        const std::size_t h = head.load(std::memory_order_relaxed);
        if (h == tail.load(std::memory_order_acquire)) return false;
        out = slots[h & (N - 1)];
        head.store(h + 1, std::memory_order_release);
        return true;
    }
};

struct Cached {
    alignas(64) std::atomic<std::size_t> head{0};
    std::size_t tail_seen = 0;  // consumer's private copy of tail
    alignas(64) std::atomic<std::size_t> tail{0};
    std::size_t head_seen = 0;  // producer's private copy of head
    alignas(64) long slots[N];

    bool push(long v) {
        const std::size_t t = tail.load(std::memory_order_relaxed);
        if (t - head_seen == N) {
            head_seen = head.load(std::memory_order_acquire);
            if (t - head_seen == N) return false;
        }
        slots[t & (N - 1)] = v;
        tail.store(t + 1, std::memory_order_release);
        return true;
    }
    bool pop(long& out) {
        const std::size_t h = head.load(std::memory_order_relaxed);
        if (h == tail_seen) {
            tail_seen = tail.load(std::memory_order_acquire);
            if (h == tail_seen) return false;
        }
        out = slots[h & (N - 1)];
        head.store(h + 1, std::memory_order_release);
        return true;
    }
};

template <class Q>
double ns_per_item(long n, long& wrong) {
    auto q = std::make_unique<Q>();
    auto t0 = std::chrono::steady_clock::now();
    std::thread producer([&] {
        for (long i = 0; i < n; ++i)
            while (!q->push(i)) {
            }
    });
    long v = 0, expect = 0;
    while (expect < n)
        if (q->pop(v)) wrong += v != expect++;
    producer.join();
    std::chrono::duration<double, std::nano> dt = std::chrono::steady_clock::now() - t0;
    return dt.count() / static_cast<double>(n);
}

int main(int argc, char** argv) {
    long n = argc > 1 ? std::atol(argv[1]) : 200000, wrong = 0;
    double a = ns_per_item<Adjacent>(n, wrong);
    double b = ns_per_item<Padded>(n, wrong);
    double c = ns_per_item<Cached>(n, wrong);
    std::printf("wrong %ld; offsets %zu %zu %zu\n", wrong, offsetof(Adjacent, tail), offsetof(Padded, tail),
                offsetof(Cached, tail));
    std::printf("ns per item: adjacent %.1f, padded %.1f, cached %.1f\n", a, b, c);
}
