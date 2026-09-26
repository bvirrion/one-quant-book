// Replays the shared fixture and compares every estimate with the Python reference's output.
#include "firm_fairprice.hpp"

#include <cassert>
#include <cmath>
#include <cstdio>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

static std::string data_dir() {
    std::string f = __FILE__;  // .../code/firm/fairprice/cpp/firm_fairprice_test.cpp
    return f.substr(0, f.rfind("/cpp/")) + "/data/";
}

static std::vector<std::vector<double>> read_csv(const std::string& path) {
    std::ifstream in(path);
    assert(in.good());
    std::vector<std::vector<double>> rows;
    std::string line;
    std::getline(in, line);  // header
    while (std::getline(in, line)) {
        std::vector<double> cells;
        std::stringstream ss(line);
        std::string c;
        while (std::getline(ss, c, ',')) cells.push_back(std::stod(c));
        rows.push_back(cells);
    }
    return rows;
}

int main() {
    const auto dir = data_dir();
    const auto par = read_csv(dir + "fixture_params.csv");  // q, r0, r1, r2
    const auto ev = read_csv(dir + "fixture_events.csv");   // t, src, y
    const auto exp = read_csv(dir + "fixture_expected.csv");  // x, p
    assert(ev.size() == exp.size() && ev.size() > 1000);
    firm::FairFilter f(par[0][0], {par[0][1], par[0][2], par[0][3]});
    for (std::size_t i = 0; i < ev.size(); ++i) {
        const double x = f.update(ev[i][0], static_cast<std::size_t>(ev[i][1]), ev[i][2]);
        assert(std::fabs(x - exp[i][0]) < 1e-9 && std::fabs(f.variance() - exp[i][1]) < 1e-12);
    }
    std::printf("fairprice C++: %zu estimates match the Python reference\n", ev.size());
    return 0;
}
