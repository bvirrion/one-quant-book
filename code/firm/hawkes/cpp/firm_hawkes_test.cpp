// Acceptance tests of firm.hawkes (C++20).
#include "firm_hawkes.hpp"
#include <cassert>
#include <cmath>
#include <vector>

using namespace firm::hawkes;

static bool near(double a, double b, double tol) { return std::fabs(a - b) < tol; }

int main() {
    const Params p{0.1, 0.7, 1.0};
    {   // log-likelihood and compensator equal the Python reference on a fixed event list
        const std::vector<double> t{0.5, 1.2, 1.3, 4.0, 4.1, 4.15, 9.0};
        assert(near(loglik(p, t, 10.0), -12.20712398254631, 1e-12));
        const auto c = compensator(p, t);
        assert(near(c[1], 0.4723902873460133, 1e-13) && near(c[6], 5.083844743294921, 1e-13));
    }
    {   // a long simulation: mean count mu T / (1 - n), residuals of mean one
        Rng rng{7};
        const double T = 200000.0;
        const auto t = simulate_thinning(p, T, rng);
        const double expected = p.mean_intensity() * T;
        assert(near(static_cast<double>(t.size()) / expected, 1.0, 0.05));
        const auto c = compensator(p, t);
        assert(near(c.back() / static_cast<double>(t.size()), 1.0, 0.02));
        // the true parameters beat a Poisson model with the same mean on the simulated data
        assert(loglik(p, t, T) > loglik(Params{p.mean_intensity(), 0.0, 1.0}, t, T));
    }
    return 0;
}
