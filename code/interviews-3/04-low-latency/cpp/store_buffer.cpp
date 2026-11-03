#include <atomic>
#include <cstdio>
#include <thread>

std::atomic<int> x, y, go{0}, done{0};
int r1, r2;

template <std::memory_order W, std::memory_order R>
long count_both_zero(long rounds) {
    long both_zero = 0;
    std::thread a([&] {
        for (long i = 1; i <= rounds; ++i) {
            while (go.load(std::memory_order_acquire) < i) {}
            x.store(1, W);
            r1 = y.load(R);
            done.fetch_add(1, std::memory_order_acq_rel);
        }
    });
    std::thread b([&] {
        for (long i = 1; i <= rounds; ++i) {
            while (go.load(std::memory_order_acquire) < i) {}
            y.store(1, W);
            r2 = x.load(R);
            done.fetch_add(1, std::memory_order_acq_rel);
        }
    });
    for (long i = 1; i <= rounds; ++i) {
        x.store(0);
        y.store(0);
        done.store(0);
        go.store(static_cast<int>(i), std::memory_order_release);
        while (done.load(std::memory_order_acquire) < 2) {}
        if (r1 == 0 && r2 == 0) ++both_zero;
    }
    a.join();
    b.join();
    go.store(0);
    return both_zero;
}

int main() {
    using enum std::memory_order;
    const long rounds = 200000;
    std::printf("relaxed %ld\n", count_both_zero<relaxed, relaxed>(rounds));
    std::printf("acq_rel %ld\n", count_both_zero<release, acquire>(rounds));
    std::printf("seq_cst %ld\n", count_both_zero<seq_cst, seq_cst>(rounds));
}
