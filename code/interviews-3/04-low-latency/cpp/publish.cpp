#include <atomic>
#include <cstdio>
#include <thread>

int payload = 0;
std::atomic<bool> ready{false};

int main() {
    std::thread writer([] {
        payload = 42;
        ready.store(true, std::memory_order_relaxed);
    });
    std::thread reader([] {
        while (!ready.load(std::memory_order_relaxed)) {
        }
        std::printf("%d\n", payload);
    });
    writer.join();
    reader.join();
}
