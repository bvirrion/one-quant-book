#include <iostream>
#include <memory>
#include <thread>
#include <vector>

int main() {
    auto root = std::make_shared<int>(5);
    std::vector<std::thread> ts;
    for (int k = 0; k < 4; ++k)
        ts.emplace_back([p = root] {             // each thread owns its own copy
            for (int i = 0; i < 2000; ++i) {
                auto q = p;
                (void)q;
            }
        });
    for (auto& t : ts) t.join();
    std::cout << root.use_count() << " " << *root << "\n";
}
