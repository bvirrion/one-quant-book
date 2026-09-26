// Chapter 8: the defined cases of the UB demos, and function multiversioning dispatching at load time.
#include <cstdio>
#include <vector>

extern "C" bool plus_one_greater(int x) { return x + 1 > x; }

__attribute__((target_clones("avx2", "default"))) double dot(const double* a, const double* b, int n) {
    double s = 0.0;
    for (int i = 0; i < n; ++i) s += a[i] * b[i];
    return s;
}

int main() {
    if (!plus_one_greater(41)) return 1;
    std::vector<double> a(1000, 0.5), b(1000, 2.0);
    if (dot(a.data(), b.data(), 1000) != 1000.0) return 1;  // exact in binary
    std::puts("ub and clones ok");
    return 0;
}
