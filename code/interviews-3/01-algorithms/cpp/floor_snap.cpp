// Reads pairs "value tick" and prints C++'s / and %, and the value snapped down to a multiple of tick.
#include <cstdint>
#include <iostream>

std::int64_t snap_down(std::int64_t x, std::int64_t tick) {
    const std::int64_t r = x % tick;     // has the sign of x
    return r < 0 ? x - r - tick : x - r;
}

int main() {
    std::int64_t x, tick;
    while (std::cin >> x >> tick) {
        std::cout << x / tick << ' ' << x % tick << ' ' << snap_down(x, tick) << '\n';
    }
}
