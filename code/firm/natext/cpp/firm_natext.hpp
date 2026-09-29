// firm::natext -- the chapter 9 kernels in C++20, free of Python: an exponentially weighted average and an as-of
// lookup over sorted times (One Quant Book 15, chapter 9). The pybind11 module (firm_natext_py.cpp) binds them to
// numpy arrays without copying; this header is also compiled and tested alone (firm_natext_test.cpp).
#pragma once

#include <cstddef>
#include <cstdint>

namespace firm::natext {

// y_0 = x_0; y_t = (1 - alpha) y_{t-1} + alpha x_t. Writes n outputs to out.
inline void ewma(const double* x, std::size_t n, double alpha, double* out) {
    if (n == 0) return;
    double y = x[0];
    out[0] = y;
    for (std::size_t i = 1; i < n; ++i) {
        y = (1.0 - alpha) * y + alpha * x[i];
        out[i] = y;
    }
}

// One step of the average: the unit the per-call benchmark calls a million times.
inline double ewma_step(double y, double x, double alpha) {
    return (1.0 - alpha) * y + alpha * x;
}

// For each left time, the index of the last right time at or before it (-1 if none).
// Both inputs sorted ascending: one merge pass, O(nl + nr).
inline void asof_index(const std::int64_t* left, std::size_t nl,
                       const std::int64_t* right, std::size_t nr, std::int64_t* out) {
    std::size_t j = 0;
    for (std::size_t i = 0; i < nl; ++i) {
        while (j < nr && right[j] <= left[i]) ++j;
        out[i] = static_cast<std::int64_t>(j) - 1;
    }
}

}  // namespace firm::natext
