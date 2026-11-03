#include <iostream>
#include <semaphore>
#include <thread>

int main() {
    std::counting_semaphore<3> slots(3);
    for (int i = 0; i < 4; ++i) std::cout << slots.try_acquire();
    std::cout << "\n";
    std::thread other([&] { slots.release(); });
    other.join();
    for (int i = 0; i < 2; ++i) std::cout << slots.try_acquire();
    std::cout << "\n";
}
