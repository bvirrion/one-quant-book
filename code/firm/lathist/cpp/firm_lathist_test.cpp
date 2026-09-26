// Acceptance test of firm.lathist, C++ side: the shared fixture's buckets and quantiles, exactly.
#include "firm_lathist.hpp"

#include <cstdio>
#include <fstream>
#include <sstream>
#include <string>

using namespace firm::lathist;

int main() {
    const std::string dir = "code/firm/lathist/data/";
    LatHist h;
    std::ifstream vf(dir + "fixture_values.csv");
    std::string line;
    std::getline(vf, line);
    while (std::getline(vf, line)) h.record(std::stoull(line));
    std::ifstream bf(dir + "fixture_buckets.csv");
    std::getline(bf, line);
    std::size_t nonzero = 0;
    while (std::getline(bf, line)) {
        const auto c = line.find(',');
        if (h.counts()[std::stoull(line.substr(0, c))] != std::stoull(line.substr(c + 1))) { std::puts("bucket mismatch"); return 1; }
        ++nonzero;
    }
    std::size_t have = 0;
    for (auto x : h.counts()) have += x != 0;
    if (have != nonzero) { std::puts("extra buckets"); return 1; }
    std::ifstream qf(dir + "fixture_quantiles.csv");
    std::getline(qf, line);
    while (std::getline(qf, line)) {
        const auto c = line.find(',');
        if (h.quantile(std::stod(line.substr(0, c))) != std::stoull(line.substr(c + 1))) { std::printf("quantile %s\n", line.c_str()); return 1; }
    }
    LatHist co;
    co.record_corrected(10000, 1000);
    if (co.count() != 9 || co.min() != 2000) { std::puts("correction"); return 1; }
    std::puts("lathist ok");
    return 0;
}
