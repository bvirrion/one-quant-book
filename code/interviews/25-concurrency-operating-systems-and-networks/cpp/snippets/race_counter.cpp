#include <cstdio>
#include <thread>

int counter = 0;  // shared, unsynchronised: every increment is a data race

void work() {
    for (int i = 0; i < 1000000; ++i) ++counter;
}

int main() {
    std::thread a(work), b(work);
    a.join();
    b.join();
    std::printf("%d\n", counter);
}
