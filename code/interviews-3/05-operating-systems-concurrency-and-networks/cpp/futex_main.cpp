#include "futex_mutex.hpp"
#include <chrono>
#include <cstdio>
#include <thread>
#include <vector>

using namespace std::chrono_literals;

int main() {
    FutexMutex m;
    for (int i = 0; i < 1000000; ++i) {          // nobody else: no system call at all
        m.lock();
        m.unlock();
    }
    std::printf("%ld %ld\n", FutexMutex::waits.load(), FutexMutex::wakes.load());
    long count = 0;
    {
        std::vector<std::thread> ts;
        for (int k = 0; k < 4; ++k)
            ts.emplace_back([&] {
                for (int i = 0; i < 100000; ++i) {
                    m.lock();
                    ++count;
                    m.unlock();
                }
            });
        for (auto& t : ts) t.join();
    }
    std::printf("%ld\n", count);
    // Two waiters behind one holder: each unlock must wake the next.
    m.lock();
    int order = 0;
    std::vector<std::thread> ts;
    for (int k = 0; k < 2; ++k)
        ts.emplace_back([&] {
            m.lock();
            ++order;
            m.unlock();
        });
    std::this_thread::sleep_for(200ms);          // both are asleep by now
    FutexMutex::waits = 0;
    m.unlock();
    for (auto& t : ts) t.join();
    std::printf("%d\n", order);
}
