// Acceptance test of firm::natext, C++ side: the kernels on small inputs worked by hand.
#include "firm_natext.hpp"

#include <cmath>
#include <cstdio>

int main() {
    const double x[4] = {10.0, 20.0, 20.0, 0.0};
    double y[4];
    firm::natext::ewma(x, 4, 0.5, y);
    const double want[4] = {10.0, 15.0, 17.5, 8.75};
    for (int i = 0; i < 4; ++i)
        if (std::fabs(y[i] - want[i]) > 1e-15) { std::puts("ewma mismatch"); return 1; }
    if (firm::natext::ewma_step(15.0, 20.0, 0.5) != 17.5) { std::puts("step mismatch"); return 1; }
    const std::int64_t left[5] = {0, 5, 10, 11, 30};
    const std::int64_t right[3] = {5, 10, 20};
    std::int64_t idx[5];
    firm::natext::asof_index(left, 5, right, 3, idx);
    const std::int64_t wantidx[5] = {-1, 0, 1, 1, 2};
    for (int i = 0; i < 5; ++i)
        if (idx[i] != wantidx[i]) { std::puts("asof mismatch"); return 1; }
    std::puts("ok");
    return 0;
}
