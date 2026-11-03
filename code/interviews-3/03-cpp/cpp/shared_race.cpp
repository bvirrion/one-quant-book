#include <iostream>
#include <memory>
#include <thread>

std::shared_ptr<int> config = std::make_shared<int>(1);

int main(int, char** argv) {
    long sum = 0;
    const char mode = argv[1][0];
    std::thread writer([&] {
        for (int i = 0; i < 2000; ++i) {
            if (mode == 'A') config = std::make_shared<int>(i);
            if (mode == 'B') std::atomic_store(&config, std::make_shared<int>(i));
        }
    });
    std::thread reader([&] {
        for (int i = 0; i < 2000; ++i) {
            if (mode == 'A') { auto p = config; sum += *p; }
            if (mode == 'B') { auto p = std::atomic_load(&config); sum += *p; }
        }
    });
    writer.join();
    reader.join();
    std::cout << (sum >= 0) << "\n";
}
