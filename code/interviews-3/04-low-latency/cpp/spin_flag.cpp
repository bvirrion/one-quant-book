#include <chrono>
#include <cstdio>
#include <thread>

bool ready = false;
int value = 0;

int main() {
    std::thread reader([] {
        while (!ready) {
        }
        std::printf("%d\n", value);
    });
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
    value = 42;
    ready = true;
    reader.join();
}
