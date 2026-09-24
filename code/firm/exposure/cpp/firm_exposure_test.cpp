// Acceptance tests of firm.exposure's C++20 kernel: the fixture shared with the Python and Rust tests.
#include "firm_exposure.hpp"
#include <cassert>
#include <cmath>

using namespace firm::exposure;

static std::vector<Matrix> fixture(int paths = 4, int steps = 12) {
    Matrix a(paths, std::vector<double>(steps + 1)), b = a;
    for (int p = 0; p < paths; ++p)
        for (int k = 0; k <= steps; ++k) {
            a[p][k] = 10.0 * std::sin(0.5 * k + p) + 0.8 * k * (p % 3 - 1);
            b[p][k] = 4.0 * std::cos(0.3 * k * (p + 1));
        }
    return {a, b};
}

static void check(const std::vector<double>& got, const std::vector<double>& want) {
    assert(got.size() == want.size());
    for (std::size_t i = 0; i < got.size(); ++i) assert(std::fabs(got[i] - want[i]) < 1e-9);
}

int main() {
    const auto f = fixture();
    {   // uncollateralised
        const auto r = aggregate(f, std::nullopt, 0.0, 0.75);
        check(r.ee, {8.7297210492, 7.5907637456, 5.6902123239, 3.7843257003, 1.8356013215, 0.5669175619, 0.0,
                     0.6360078225, 1.5098125690, 2.4449258520, 4.3102173514, 5.7459430907, 6.9298835214});
        check(r.pfe, {12.4147098481, 9.2711613141, 10.1160523077, 5.0759130623, 0.0, 0.0, 0.0, 0.0, 0.0,
                      1.4026801419, 5.2689983012, 5.9521302487, 9.0032712453});
    }
    {   // threshold 2, MTA 1, one-step margin period of risk
        const auto r = aggregate(f, Csa{2.0, 1.0, 1}, 0.0, 0.75);
        check(r.ee, {8.7297210492, 7.5907637456, 1.0751127413, 0.4863343579, 0.3307720073, 0.8061311759,
                     0.6054963792, 0.6986256332, 1.5724303798, 2.5579884072, 3.3451194729, 2.9125051166,
                     3.4386424443});
        check(r.ene, {0.0, -0.7146003147, -4.5050641168, -3.4844349494, -2.6547181597, -2.8014907644,
                      -2.5631337253, -3.4440248131, -2.1206767566, -1.4184974824, -0.7394057471,
                      -0.5185809837, -1.7316228823});
    }
    {   // zero threshold, two-step lag, independent amount 1.5
        const auto r = aggregate(f, Csa{0.0, 0.0, 2}, 1.5, 0.75);
        check(r.ee, {7.2297210492, 6.4657637456, 4.5652123239, 0.1864470991, 0.0, 1.7619031832, 2.4957711161,
                     1.9628207594, 1.8013833311, 3.8703348909, 4.9274378445, 3.4287434730, 4.2039217668});
        check(r.pfe, {10.9147098481, 7.7711613141, 8.6160523077, 0.0, 0.0, 0.0, 4.2045873756, 0.1887673735,
                      0.4158118055, 5.4286348775, 7.5378837372, 4.7462118913, 6.2909179008});
    }
    return 0;
}
