// Chapter 22: what a pre-trade check costs. Replays firm.riskgate's fixture (12 checks on every order, outcomes of
// every kind) timing each check with the TSC, then a stream where every order passes; prints quantiles in ns.
#include <cstdio>
#include <fstream>
#include <map>
#include <sstream>
#include <string>
#include <vector>

#include "firm_riskgate.hpp"
#include "firm_ubench.hpp"

using namespace firm::risk;
namespace ub = firm::ubench;

static std::string slurp(const std::string& p) {
    std::ifstream f(p);
    std::stringstream s;
    s << f.rdbuf();
    return s.str();
}

int main() {
    const std::string D = "code/firm/riskgate/data/";
    Names names;
    const auto j = firm::exchsim::json::parse(slurp(D + "limits.json"));
    std::map<int, Limits> lim;
    for (const auto& [k, v] : j.o) lim[std::stoi(k)] = parse_limits(v, names);
    const ub::Clock clk = ub::Clock::calibrate();
    const double ovh = clk.ns(ub::overhead());
    std::vector<double> acc, ref, all;
    for (int pass = 0; pass < 5; ++pass) {
        Gate g(lim.at(1), 0);
        std::istringstream in(slurp(D + "events.txt"));
        std::string line;
        bool first = true;
        while (std::getline(in, line)) {
            std::istringstream l(line);
            std::int64_t t;
            std::string k, a, b;
            l >> t >> k;
            if (k == "L") {
                int v;
                l >> v;
                if (first) g = Gate(lim.at(v), t), first = false;
                else g.set_limits(t, lim.at(v));
            } else if (k == "H") g.heartbeat(t);
            else if (k == "P") {
                std::uint32_t i;
                std::int64_t p;
                l >> i >> p;
                g.set_reference(t, i, p);
            } else if (k == "O") {
                std::uint64_t cl;
                std::uint32_t i;
                std::int64_t q, p;
                l >> cl >> a >> i >> b >> q >> p;
                const int s = names.find(names.strat, a);
                const std::uint64_t t0 = ub::tsc_start();
                const Decision d = g.check(t, s, i, b[0], q, p, cl);
                const double ns = clk.ns(ub::rdtscp() - t0) - ovh;
                ub::do_not_optimize(d);
                if (pass) (d.code == '.' ? acc : ref).push_back(ns), all.push_back(ns);
            } else if (k == "F") {
                std::uint64_t cl;
                std::int64_t q, p;
                l >> cl >> q >> p;
                g.on_fill(cl, q, p);
            } else if (k == "X") {
                std::uint64_t cl;
                l >> cl;
                g.on_done(cl);
            }
        }
    }
    // every order passes: generous limits, each order finished right after its check (untimed); with the
    // duplicate check off (dup_ns = 0) and on (a 1 ns window that never matches)
    std::vector<double> pass[2];
    for (int dup = 0; dup < 2; ++dup) {
        Limits wide = lim.at(1);
        for (auto& s : wide.strat) s.rate = 1'000'000'000, s.burst = 1'000'000, s.max_open = 1'000'000;
        wide.dup_ns = dup, wide.max_age = wide.ref_max_age = 1LL << 60;
        Gate g(wide, 0);
        g.set_reference(0, 1, 1'000'000);
        for (int i = 0; i < 200'000; ++i) {
            const auto cl = static_cast<std::uint64_t>(i) + 1;
            const std::uint64_t t0 = ub::tsc_start();
            const Decision d = g.check(i, 0, 1, (i & 1) ? 'B' : 'S', 100, 1'000'000, cl);
            const double ns = clk.ns(ub::rdtscp() - t0) - ovh;
            ub::do_not_optimize(d);
            g.on_done(cl);
            if (i >= 1000) pass[dup].push_back(ns);
        }
    }
    const std::pair<const char*, std::vector<double>*> cases[] = {
        {"fixture: all", &all}, {"fixture: accepted", &acc}, {"fixture: refused", &ref},
        {"all accepted", &pass[0]}, {"all accepted: duplicate check on", &pass[1]}};
    for (const auto& [name, v] : cases)
        for (const double q : {0.5, 0.99}) std::printf("check,%s,%g,%.1f,%zu\n", name, q, ub::quantile(*v, q), v->size());
    return 0;
}
