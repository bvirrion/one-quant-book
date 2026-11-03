#include <cstdio>
#include <mutex>
#include <thread>

std::mutex m;
long total = 0;

void add(long n) {
    std::lock_guard<std::mutex>{m};
    total += n;
}

int main() {
    auto work = [] { for (int i = 0; i < 100000; ++i) add(1); };
    std::thread a(work), b(work);
    a.join();
    b.join();
    std::printf("%ld\n", total);
}
