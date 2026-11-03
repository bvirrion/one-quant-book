#include <atomic>
#include <cstdio>
#include <thread>
#include <vector>

class SpinLock {
    std::atomic<bool> held_{false};

public:
    void lock() {
        while (held_.exchange(true, std::memory_order_relaxed)) {
        }
    }
    void unlock() { held_.store(false, std::memory_order_relaxed); }
};

SpinLock guard;
long counter = 0;

int main() {
    std::vector<std::thread> pool;
    for (int t = 0; t < 4; ++t)
        pool.emplace_back([] {
            for (int i = 0; i < 20000; ++i) {
                guard.lock();
                ++counter;
                guard.unlock();
            }
        });
    for (auto& th : pool) th.join();
    std::printf("%ld\n", counter);
}
