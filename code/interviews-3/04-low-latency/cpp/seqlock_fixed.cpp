#include <atomic>
#include <bit>
#include <cstdint>
#include <cstdio>
#include <thread>

struct Quote {
    double bid, ask;
};

class SeqLock {
    std::atomic<unsigned> seq_{0};
    std::atomic<std::uint64_t> bid_{std::bit_cast<std::uint64_t>(0.0)};
    std::atomic<std::uint64_t> ask_{std::bit_cast<std::uint64_t>(1.0)};

public:
    void write(const Quote& q) {  // exactly one writer thread
        unsigned s = seq_.load(std::memory_order_relaxed);
        seq_.store(s + 1, std::memory_order_relaxed);
        std::atomic_thread_fence(std::memory_order_release);
        bid_.store(std::bit_cast<std::uint64_t>(q.bid), std::memory_order_relaxed);
        ask_.store(std::bit_cast<std::uint64_t>(q.ask), std::memory_order_relaxed);
        seq_.store(s + 2, std::memory_order_release);
    }
    Quote read() const {
        for (;;) {
            unsigned s1 = seq_.load(std::memory_order_acquire);
            if (s1 & 1) continue;
            Quote copy{std::bit_cast<double>(bid_.load(std::memory_order_relaxed)),
                       std::bit_cast<double>(ask_.load(std::memory_order_relaxed))};
            std::atomic_thread_fence(std::memory_order_acquire);
            unsigned s2 = seq_.load(std::memory_order_relaxed);
            if (s1 == s2) return copy;
        }
    }
};

SeqLock lock_;
std::atomic<bool> stop{false};

int main() {
    std::thread writer([] {
        for (int i = 1; i <= 200000; ++i) lock_.write(Quote{double(i), double(i) + 1.0});
        stop.store(true);
    });
    long torn = 0;
    while (!stop.load()) {
        Quote q = lock_.read();
        torn += q.ask != q.bid + 1.0;
    }
    writer.join();
    std::printf("%ld\n", torn);
}
