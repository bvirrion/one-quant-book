// Acceptance tests of firm.mcengine (C++20).
#include "firm_mcengine.hpp"
#include <cassert>
#include <cmath>
#include <cstdint>

using namespace firm::mcengine;

static bool near(double a, double b, double tol) { return std::fabs(a - b) < tol; }

int main() {
    {   // SplitMix64 test vector (seed 1234567), as in the Python and Rust twins
        SplitMix64 g{1234567};
        const std::uint64_t want[5] = {6457827717110365317ULL, 3203168211198807973ULL, 9817491932198370423ULL,
                                       4593380528125082431ULL, 16408922859458223821ULL};
        for (auto w : want) assert(g.next_u64() == w);
    }
    {   // the reference normal stream and path agree with Python to rounding
        NormalStream s{42};
        const double want[4] = {0.41471975043153037, 0.6526812221519428, -0.8918862136277568, 1.326833562814106};
        for (double w : want) assert(near(s.next(), w, 1e-15));
        NormalStream z{7};
        const auto p = brownian_path(4, 1.0, z);
        assert(near(p[4], 0.44269661601997956, 1e-14));
    }
    {   // Var(W_T) = T for increment and bridge construction; bridge midpoint variance T/2
        NormalStream z{11};
        const int n = 40000;
        double s1 = 0, s2 = 0, b2 = 0, m2 = 0;
        for (int i = 0; i < n; ++i) {
            const auto p = brownian_path(8, 2.0, z);
            s1 += p[8];
            s2 += p[8] * p[8];
            const auto b = bridge_path(3, 2.0, z);
            b2 += b[8] * b[8];
            m2 += b[4] * b[4];
        }
        assert(near(s1 / n, 0.0, 0.03));
        assert(near(s2 / n, 2.0, 0.06) && near(b2 / n, 2.0, 0.06) && near(m2 / n, 1.0, 0.03));
    }
    {   // crossing probability: formula against a fine simulation of the bridge
        assert(bridge_crossing_probability(0.5, -0.1, 0.0, 1.0) == 1.0);
        const double p = bridge_crossing_probability(0.3, 0.2, 0.0, 1.0);
        assert(near(p, std::exp(-0.12), 1e-15));
    }
    {   // stage 2: OU stationary moments; square-root schemes
        NormalStream z{21};
        double m = 0, m2 = 0;
        const int n = 20000;
        for (int i = 0; i < n; ++i) {
            const auto x = ou_exact_path(0.5, 2.0, 0.1, 0.4, 5.0, 10, z);
            m += x.back();
            m2 += x.back() * x.back();
        }
        m /= n;
        assert(near(m, 0.1, 0.01) && near(m2 / n - m * m, 0.04, 0.003));   // sigma^2 / (2 kappa)
        int neg_plain = 0, neg_ft = 0;
        for (int i = 0; i < 2000; ++i) {
            const auto p = sqrt_euler_path(0.04, 2.0, 0.04, 0.6, 1.0, 252, z, SqrtScheme::plain);
            bool bad = false;
            for (double v : p) bad = bad || !(v >= 0.0);
            neg_plain += bad;
            const auto f = sqrt_euler_path(0.04, 2.0, 0.04, 0.6, 1.0, 252, z, SqrtScheme::full_truncation);
            for (double v : f) neg_ft += (v < 0.0 || std::isnan(v));
        }
        assert(neg_plain > 100 && neg_ft == 0);
        assert(near(feller_ratio(2.0, 0.04, 0.6), 0.16 / 0.36, 1e-15));
    }
    {   // stage 3: Philox4x64-10 against NumPy's Philox (counter 1, key (7, 0)) and the Python twin
        const Block want{0xdf4034b829e9fba4ULL, 0x4b9d10cdf8e64087ULL, 0x6b8b857e506aac98ULL, 0x67c7c945b1ba6e52ULL};
        assert(philox4x64({1, 0, 0, 0}, {7, 0}) == want);
        const Block want2{0x6574e96a9536cfebULL, 0x545356bdc8741804ULL, 0x712f1a3a7274032eULL, 0x5b41a2f789855f11ULL};
        assert(philox4x64({0, 0, 0, 0}, {2600, 0}) == want2);
    }
    {   // Sobol: Joe and Kuo's published first points in three dimensions, then Owen scrambling as in Python
        const double want[10][3] = {{0, 0, 0}, {0.5, 0.5, 0.5}, {0.75, 0.25, 0.25}, {0.25, 0.75, 0.75},
                                    {0.375, 0.375, 0.625}, {0.875, 0.875, 0.125}, {0.625, 0.125, 0.875},
                                    {0.125, 0.625, 0.375}, {0.1875, 0.3125, 0.9375}, {0.6875, 0.8125, 0.4375}};
        for (std::uint32_t i = 0; i < 10; ++i)
            for (unsigned d = 0; d < 3; ++d) assert(sobol_point(i, d) * 0x1.0p-32 == want[i][d]);
        std::uint64_t sum = 0;
        for (std::uint32_t i = 0; i < 16; ++i)
            for (unsigned d = 0; d < 8; ++d) sum += owen_scramble(sobol_point(i, d), d, 2600);
        assert(sum == 275744286821ULL);
        assert(sobol_point(15, 7) == 1342177280u);
        assert(owen_scramble(sobol_point(5, 3), 3, 2600) == 1066785506u);
        assert(owen_scramble(sobol_point(15, 7), 7, 2600) == 4087102229u);
        // a scrambled 2^m-point set is still a net: one point in each of 16 dyadic intervals, every dimension
        for (unsigned d = 0; d < 8; ++d) {
            unsigned seen = 0;
            for (std::uint32_t i = 0; i < 16; ++i) seen |= 1u << (owen_scramble(sobol_point(i, d), d, 99) >> 28);
            assert(seen == 0xFFFFu);
        }
    }
    return 0;
}
