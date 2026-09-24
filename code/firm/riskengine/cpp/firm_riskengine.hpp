// firm.riskengine aggregation kernel (C++20 twin of firm_riskengine.py): P&L of every node of the risk
// hierarchy, historical VaR and ES (k-th largest loss, k = ceil((1 - a) n)), Euler contributions of ES.
#pragma once
#include <algorithm>
#include <cmath>
#include <map>
#include <numeric>
#include <string>
#include <utility>
#include <vector>

namespace firm::riskengine {

using Matrix = std::vector<std::vector<double>>;   // pnl[scenario][trade]
using Path = std::vector<std::string>;

inline std::vector<Path> nodes(const std::vector<Path>& paths) {
    std::vector<Path> out;
    for (const auto& p : paths)
        for (std::size_t i = 1; i <= p.size(); ++i) out.emplace_back(p.begin(), p.begin() + i);
    std::sort(out.begin(), out.end(), [](const Path& a, const Path& b) {
        return a.size() != b.size() ? a.size() < b.size() : a < b;
    });
    out.erase(std::unique(out.begin(), out.end()), out.end());
    return out;
}

inline bool under(const Path& p, const Path& n) {
    return p.size() >= n.size() && std::equal(n.begin(), n.end(), p.begin());
}

inline std::map<Path, std::vector<double>> aggregate(const Matrix& pnl, const std::vector<Path>& paths) {
    std::map<Path, std::vector<double>> agg;
    for (const auto& n : nodes(paths)) {
        std::vector<double> v(pnl.size(), 0.0);
        for (std::size_t s = 0; s < pnl.size(); ++s)
            for (std::size_t j = 0; j < paths.size(); ++j)
                if (under(paths[j], n)) v[s] += pnl[s][j];
        agg.emplace(n, std::move(v));
    }
    return agg;
}

inline std::size_t tail_count(std::size_t n, double level) {
    const auto k = static_cast<std::size_t>(std::ceil((1.0 - level) * static_cast<double>(n) - 1e-9));
    return std::max<std::size_t>(1, k);
}

// (VaR, ES) as positive losses at one level.
inline std::pair<double, double> var_es(const std::vector<double>& pnl, double level) {
    std::vector<double> loss(pnl.size());
    std::transform(pnl.begin(), pnl.end(), loss.begin(), [](double x) { return -x; });
    std::sort(loss.begin(), loss.end(), std::greater<>());
    const auto k = tail_count(loss.size(), level);
    return {loss[k - 1], std::accumulate(loss.begin(), loss.begin() + k, 0.0) / static_cast<double>(k)};
}

// Each child's average loss in the parent's k worst scenarios (stable order on ties).
inline std::map<Path, double> euler_es(const std::vector<double>& parent,
                                       const std::map<Path, std::vector<double>>& children, double level) {
    std::vector<std::size_t> idx(parent.size());
    std::iota(idx.begin(), idx.end(), 0);
    std::stable_sort(idx.begin(), idx.end(), [&](std::size_t a, std::size_t b) { return parent[a] < parent[b]; });
    const auto k = tail_count(parent.size(), level);
    std::map<Path, double> out;
    for (const auto& [c, v] : children) {
        double s = 0.0;
        for (std::size_t i = 0; i < k; ++i) s += v[idx[i]];
        out[c] = -s / static_cast<double>(k);
    }
    return out;
}

}  // namespace firm::riskengine
