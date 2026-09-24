// firm.exposure -- aggregation kernel (build of One Quant Book 6, chapter 17), C++20 twin of the
// netting / collateral / profile step of firm_exposure.py: values[trade][path][time] are summed into
// the netting set, a two-way CSA (threshold, minimum transfer amount) sets the collateral held, the
// exposure at t uses the collateral of `lag` steps earlier, and EE, ENE and PFE (lower quantile) are
// computed per time. Header only, no dependencies.
#pragma once
#include <algorithm>
#include <cmath>
#include <optional>
#include <vector>

namespace firm::exposure {

using Matrix = std::vector<std::vector<double>>;   // [path][time]

struct Csa {
    double threshold = 0.0;
    double mta = 0.0;
    int lag = 0;
};

struct Profiles {
    std::vector<double> ee, ene, pfe;
};

inline Matrix net(const std::vector<Matrix>& trades) {
    Matrix v = trades.at(0);
    for (std::size_t j = 1; j < trades.size(); ++j)
        for (std::size_t p = 0; p < v.size(); ++p)
            for (std::size_t k = 0; k < v[p].size(); ++k) v[p][k] += trades[j][p][k];
    return v;
}

inline Matrix collateral(const Matrix& v, double threshold, double mta) {
    Matrix c(v.size(), std::vector<double>(v.at(0).size(), 0.0));
    for (std::size_t p = 0; p < v.size(); ++p)
        for (std::size_t k = 1; k < v[p].size(); ++k) {
            const double x = v[p][k];
            const double target = x > threshold ? x - threshold : (x < -threshold ? x + threshold : 0.0);
            c[p][k] = std::fabs(target - c[p][k - 1]) >= mta ? target : c[p][k - 1];
        }
    return c;
}

inline Profiles aggregate(const std::vector<Matrix>& trades, std::optional<Csa> csa, double ia, double q) {
    const Matrix v = net(trades);
    const std::size_t np = v.size(), nt = v.at(0).size();
    Matrix e = v;
    if (csa) {
        const Matrix c = collateral(v, csa->threshold, csa->mta);
        for (std::size_t p = 0; p < np; ++p)
            for (std::size_t k = 0; k < nt; ++k) {
                const auto lag = static_cast<std::size_t>(csa->lag);
                e[p][k] = v[p][k] - (k >= lag ? c[p][k - lag] : 0.0);
            }
    }
    Profiles out{std::vector<double>(nt), std::vector<double>(nt), std::vector<double>(nt)};
    std::vector<double> pos(np);
    for (std::size_t k = 0; k < nt; ++k) {
        double s = 0.0, sn = 0.0;
        for (std::size_t p = 0; p < np; ++p) {
            pos[p] = std::max(e[p][k] - ia, 0.0);
            s += pos[p];
            sn += std::min(e[p][k], 0.0);
        }
        out.ee[k] = s / static_cast<double>(np);
        out.ene[k] = sn / static_cast<double>(np);
        std::sort(pos.begin(), pos.end());
        out.pfe[k] = pos[static_cast<std::size_t>(std::floor(q * static_cast<double>(np - 1)))];
    }
    return out;
}

}  // namespace firm::exposure
