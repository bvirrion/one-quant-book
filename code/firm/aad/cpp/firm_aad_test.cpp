// Acceptance tests of firm.aad (C++20): the 400-input test function of the Python and Rust twins; reverse mode
// against forward mode and against bumping; the cost of the gradient in evaluations.
#include "firm_aad.hpp"
#include <cassert>
#include <chrono>
#include <cmath>
#include <vector>

using namespace firm::aad;

template <class T>
T F(const std::vector<T>& z) {
    const std::size_t n = z.size();
    std::vector<T> D;
    D.reserve(n);
    for (std::size_t i = 0; i < n; ++i) D.push_back(exp(-(z[i] * (0.075 * static_cast<double>(i + 1)))));
    T tot = D[0] * 1.0;
    for (std::size_t i = 1; i < n; ++i) {
        const double w = 1.0 + static_cast<double>(i % 7);
        tot = tot + D[i] * w;
        tot = tot + ncdf((log(D[i - 1] / D[i]) - 0.002) / 0.05) * w;
    }
    return tot;
}

static double Fd(const std::vector<double>& z) {
    const std::size_t n = z.size();
    std::vector<double> D(n);
    for (std::size_t i = 0; i < n; ++i) D[i] = std::exp(-(z[i] * (0.075 * static_cast<double>(i + 1))));
    double tot = D[0] * 1.0;
    for (std::size_t i = 1; i < n; ++i) {
        const double w = 1.0 + static_cast<double>(i % 7);
        tot = tot + D[i] * w;
        tot = tot + ncdf((std::log(D[i - 1] / D[i]) - 0.002) / 0.05) * w;
    }
    return tot;
}

int main() {
    const std::size_t n = 400;
    std::vector<double> z(n);
    for (std::size_t i = 0; i < n; ++i) z[i] = 0.03 + 0.0001 * static_cast<double>(i);
    tape.clear();
    std::vector<Var> zv(z.begin(), z.end());
    const Var y = F(zv);
    tape.reverse(y.idx);
    // the Python twin's value and gradient components
    assert(std::fabs(y.v - 1643.8656977694293) < 1e-9);
    assert(std::fabs(zv[0].adjoint() + 1.2716414715908044) < 1e-10);
    assert(std::fabs(zv[17].adjoint() + 15.944508608229377) < 1e-10);
    assert(std::fabs(zv[399].adjoint() - 233.82677751949) < 1e-9);
    // forward mode and central bumps agree
    for (std::size_t k : {0u, 17u, 200u, 399u}) {
        std::vector<Dual> zd(n);
        for (std::size_t i = 0; i < n; ++i) zd[i] = {z[i], i == k ? 1.0 : 0.0};
        assert(std::fabs(F(zd).d - zv[k].adjoint()) < 1e-10);
        auto up = z, dn = z;
        up[k] += 1e-6;
        dn[k] -= 1e-6;
        assert(std::fabs((Fd(up) - Fd(dn)) / 2e-6 - zv[k].adjoint()) < 1e-5 * (1 + std::fabs(zv[k].adjoint())));
    }
    // cost: one taped evaluation plus one sweep, against one plain evaluation (loose bound; timings vary)
    using clk = std::chrono::steady_clock;
    const int reps = 200;
    double sink = 0.0;
    auto t0 = clk::now();
    for (int r = 0; r < reps; ++r) sink += Fd(z);
    auto t1 = clk::now();
    for (int r = 0; r < reps; ++r) {
        tape.clear();
        std::vector<Var> v(z.begin(), z.end());
        const Var out = F(v);
        tape.reverse(out.idx);
        sink += v[3].adjoint();
    }
    auto t2 = clk::now();
    const double ratio = std::chrono::duration<double>(t2 - t1).count() / std::chrono::duration<double>(t1 - t0).count();
    assert(sink != 0.0 && ratio < 20.0);
    return 0;
}
