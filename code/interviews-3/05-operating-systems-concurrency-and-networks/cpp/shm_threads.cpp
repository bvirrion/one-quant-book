// Not printed: the same ring between two threads, so that ThreadSanitizer can see it.
#include "shm_ring.hpp"
#include <cstdio>
#include <thread>

int main() {
    static ShmRing<64> ring;
    std::thread producer([] {
        for (std::uint64_t i = 0; i < 200000; ++i)
            while (!ring.push(i)) {}
    });
    std::uint64_t expected = 0, v;
    long bad = 0;
    while (expected < 200000)
        if (ring.pop(v)) bad += v != expected++;
    producer.join();
    std::printf("%ld\n", bad);
}
