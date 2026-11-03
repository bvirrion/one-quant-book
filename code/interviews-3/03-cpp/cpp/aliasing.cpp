#include <bit>
#include <cstdint>
#include <iostream>

[[gnu::noinline]] int store_both(int* a, float* b) {
    *a = 1;
    *b = 0.0f;
    return *a;
}

int main() {
    int x = 0;
    std::cout << store_both(&x, reinterpret_cast<float*>(&x)) << "\n";
    std::cout << std::hex << std::bit_cast<std::uint32_t>(1.0f) << "\n";
}
