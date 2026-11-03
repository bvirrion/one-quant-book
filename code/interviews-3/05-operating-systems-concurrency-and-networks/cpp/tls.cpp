#include <atomic>
#include <iostream>
#include <thread>
#include <vector>

std::atomic<long> shared{0};
thread_local long mine = 0;

int main() {
    std::atomic<long> most{0};
    std::vector<std::thread> ts;
    for (int k = 0; k < 4; ++k)
        ts.emplace_back([&] {
            for (int i = 0; i < 1000; ++i) {
                ++shared;
                ++mine;
            }
            if (mine > most) most = mine;
        });
    for (auto& t : ts) t.join();
    std::cout << shared << " " << most << " " << mine << "\n";
}
