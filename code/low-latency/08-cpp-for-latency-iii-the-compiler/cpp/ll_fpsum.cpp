// Chapter 8: a floating-point sum whose result depends on the order of the additions. -ffast-math lets the compiler
// reorder them (to vectorise), so the checksum changes: firm.flagbench refuses to rank that flag set.
#include <chrono>
#include <cstdio>
#include <vector>

int main() {
    std::vector<float> v(1 << 20);
    for (std::size_t i = 0; i < v.size(); ++i) v[i] = 1.0f / static_cast<float>(i + 1);
    float s = 0.0f;
    const auto t0 = std::chrono::steady_clock::now();
    for (int r = 0; r < 20; ++r) {
        s = 0.0f;
        for (float x : v) s += x;
    }
    const double ns = std::chrono::duration<double, std::nano>(std::chrono::steady_clock::now() - t0).count();
    std::printf("%.9g\n%.4f\n", s, ns / (20.0 * static_cast<double>(v.size())));
    return 0;
}
