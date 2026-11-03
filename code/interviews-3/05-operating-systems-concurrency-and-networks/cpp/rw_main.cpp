#include "rwlock.hpp"
#include <atomic>
#include <chrono>
#include <cstdio>
#include <thread>
#include <vector>

using namespace std::chrono_literals;

int main() {
    RwLock lock;
    long a = 0, b = 0;                           // a writer keeps a == b
    std::atomic<long> bad{0};
    std::atomic<int> inside_w{0};
    {
        std::vector<std::thread> ts;
        for (int k = 0; k < 2; ++k)
            ts.emplace_back([&] {
                for (int i = 0; i < 5000; ++i) {
                    lock.lock();
                    if (++inside_w != 1) ++bad;
                    ++a;
                    ++b;
                    --inside_w;
                    lock.unlock();
                }
            });
        for (int k = 0; k < 4; ++k)
            ts.emplace_back([&] {
                for (int i = 0; i < 5000; ++i) {
                    lock.lock_shared();
                    if (a != b || inside_w != 0) ++bad;
                    lock.unlock_shared();
                }
            });
        for (auto& t : ts) t.join();
    }
    std::printf("%ld %ld\n", bad.load(), a);
    // A reader holds it; a writer arrives; a new reader must now wait.
    lock.lock_shared();
    std::thread writer([&] { lock.lock(); ++a; lock.unlock(); });
    std::this_thread::sleep_for(100ms);
    int overtook = lock.try_lock_shared();
    std::printf("%d\n", overtook);
    if (overtook) lock.unlock_shared();
    lock.unlock_shared();
    writer.join();
    std::printf("%d %ld\n", lock.try_lock_shared(), a);
}
