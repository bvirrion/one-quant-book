// Chapter 4: the ping-pong terminates and returns a positive time (no timing is asserted).
#include "ll_c2c.hpp"

#include <cstdio>

int main() {
    const unsigned n = std::thread::hardware_concurrency();
    const double ns = ll::c2c::one_way_ns(0, n > 1 ? 1 : 0, 2000);
    if (!(ns > 0.0)) return 1;
    std::puts("c2c ok");
    return 0;
}
