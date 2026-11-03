#include <cstdio>
#include <mutex>
#include <thread>
#include <vector>

struct Config { long limit = 1000; };

Config* instance = nullptr;
std::mutex m;

Config* get() {
    if (instance == nullptr) {
        std::lock_guard lock(m);
        if (instance == nullptr) instance = new Config;
    }
    return instance;
}

int main() {
    std::vector<std::thread> pool;
    for (int i = 0; i < 4; ++i) pool.emplace_back([] { (void) get()->limit; });
    for (auto& t : pool) t.join();
    std::printf("%ld\n", get()->limit);
}
