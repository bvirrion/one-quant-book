#include <atomic>
#include <bit>
#include <cstddef>
#include <cstdio>
#include <thread>

template <class T, std::size_t N>
class Spsc {
    static_assert(std::has_single_bit(N));
    alignas(64) std::atomic<std::size_t> head_{0};  // written by the consumer only
    alignas(64) std::atomic<std::size_t> tail_{0};  // written by the producer only
    alignas(64) T slots_[N];

public:
    bool push(const T& v) {
        const std::size_t t = tail_.load(std::memory_order_relaxed);
        if (t - head_.load(std::memory_order_acquire) == N) return false;
        slots_[t & (N - 1)] = v;
        tail_.store(t + 1, std::memory_order_release);
        return true;
    }
    bool pop(T& out) {
        const std::size_t h = head_.load(std::memory_order_relaxed);
        if (h == tail_.load(std::memory_order_acquire)) return false;
        out = slots_[h & (N - 1)];
        head_.store(h + 1, std::memory_order_release);
        return true;
    }
};

Spsc<long, 8> q;

int main() {
    const long n = 200000;
    std::thread producer([] {
        for (long i = 0; i < n; ++i)
            while (!q.push(i)) {
            }
    });
    long v = 0, expect = 0, wrong = 0;
    while (expect < n)
        if (q.pop(v)) wrong += v != expect++;
    producer.join();
    std::printf("%ld wrong of %ld\n", wrong, expect);
}
