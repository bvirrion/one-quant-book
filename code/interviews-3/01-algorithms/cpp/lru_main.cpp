// Drives Lru from standard input, so that the test can compare it with a model: "capacity", then "g key" or "p key value".
#include <cstdio>
#include <iostream>
#include <string>

#include "lru.hpp"

int main() {
    std::size_t capacity = 0;
    std::cin >> capacity;
    Lru<long, long> cache(capacity);
    std::string op;
    while (std::cin >> op) {
        long key = 0;
        std::cin >> key;
        if (op == "g") {
            const auto got = cache.get(key);
            std::printf("%ld\n", got ? *got : -1L);
        } else {
            long value = 0;
            std::cin >> value;
            cache.put(key, value);
        }
    }
}
