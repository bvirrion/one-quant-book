// Checks the C++20 egress queue against the Python reference's fixture (data/fixture_egress.csv, written by
// make_netsim_fixture.py): same drops, same departures to the nanosecond, same maximum backlog.
#include <cmath>
#include <cstdio>
#include <fstream>
#include <sstream>
#include <string>

#include "firm_netsim.hpp"

int main() {
    std::string here = __FILE__;
    const std::string dir = here.substr(0, here.rfind('/') + 1);
    std::ifstream in(dir + "../data/fixture_egress.csv");
    if (!in) { std::puts("missing fixture"); return 1; }
    std::string line;
    std::getline(in, line);   // header: gbps,buffer,max_backlog,n_dropped
    std::getline(in, line);
    double gbps = 0, buffer = 0, max_backlog = 0;
    long long n_dropped = 0;
    std::sscanf(line.c_str(), "%lf,%lf,%lf,%lld", &gbps, &buffer, &max_backlog, &n_dropped);
    std::getline(in, line);   // header: t_ns,frame,depart_ns
    std::vector<std::int64_t> t, f;
    std::vector<double> dep;
    while (std::getline(in, line)) {
        long long a = 0, b = 0;
        double d = 0;
        if (std::sscanf(line.c_str(), "%lld,%lld,%lf", &a, &b, &d) != 3) continue;
        t.push_back(a), f.push_back(b), dep.push_back(d);
    }
    const auto r = firm::netsim::egress(t, f, gbps, buffer);
    int bad = 0;
    for (std::size_t i = 0; i < t.size(); ++i)
        if (std::fabs(r.depart_ns[i] - dep[i]) > 0.5) ++bad;
    if (r.n_dropped != n_dropped || std::fabs(r.max_backlog - max_backlog) > 1e-6 || bad) {
        std::printf("mismatch: dropped %lld vs %lld, max %.3f vs %.3f, %d departures\n",
                    static_cast<long long>(r.n_dropped), n_dropped, r.max_backlog, max_backlog, bad);
        return 1;
    }
    std::printf("netsim egress: %zu frames, %lld dropped, identical to the Python reference\n", t.size(), n_dropped);
    return 0;
}
