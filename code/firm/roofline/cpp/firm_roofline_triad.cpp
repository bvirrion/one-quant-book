// firm.roofline -- one core's memory bandwidth by the STREAM triad a[i] = b[i] + s * c[i] (One Quant Book 15, ch. 14).
// Usage: firm_roofline_triad N REPEATS   -> prints the best bandwidth in GB/s, counting 24 bytes per element.
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <vector>

int main(int argc, char** argv) {
    const std::size_t n = argc > 1 ? std::strtoull(argv[1], nullptr, 10) : (1u << 24);
    const int reps = argc > 2 ? std::atoi(argv[2]) : 10;
    std::vector<double> a(n, 0.0), b(n, 1.0), c(n, 2.0);
    const double s = 3.0;
    double best = 1e30;
    for (int r = 0; r < reps; ++r) {
        auto t0 = std::chrono::steady_clock::now();
        for (std::size_t i = 0; i < n; ++i) a[i] = b[i] + s * c[i];
        auto t1 = std::chrono::steady_clock::now();
        double dt = std::chrono::duration<double>(t1 - t0).count();
        if (dt < best) best = dt;
        b[r % n] = a[(r * 7) % n];           // keep the loop from being optimised away
    }
    std::printf("%.3f %.9f\n", 24.0 * static_cast<double>(n) / best / 1e9, a[n / 2]);
    return 0;
}
