// Chapter 4 benchmark: one-way core-to-core latency for every pair of CPUs, best of three runs.
// Output: a,b,ns (both orders, and the diagonal as 0 for the heat map).
#include <algorithm>
#include <cstdio>
#include <string>

#include "ll_c2c.hpp"

int main(int argc, char** argv) {
    const int n = static_cast<int>(std::thread::hardware_concurrency());
    const int trips = argc > 1 ? std::stoi(argv[1]) : 20000;
    std::vector<double> m(static_cast<std::size_t>(n * n), 0.0);
    for (int a = 0; a < n; ++a)
        for (int b = a + 1; b < n; ++b) {
            double best = 1e300;
            for (int r = 0; r < 3; ++r) best = std::min(best, ll::c2c::one_way_ns(a, b, trips));
            m[static_cast<std::size_t>(a * n + b)] = m[static_cast<std::size_t>(b * n + a)] = best;
        }
    std::printf("a,b,ns\n");
    for (int a = 0; a < n; ++a)
        for (int b = 0; b < n; ++b) std::printf("%d,%d,%.1f\n", a, b, m[static_cast<std::size_t>(a * n + b)]);
    return 0;
}
