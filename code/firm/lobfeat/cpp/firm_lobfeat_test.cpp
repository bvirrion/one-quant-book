// Replays the shared fixture and compares every feature with the Python reference's output.
#include "firm_lobfeat.hpp"

#include <cassert>
#include <cmath>
#include <cstdio>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

static std::string data_dir() {
    std::string f = __FILE__;                       // .../code/firm/lobfeat/cpp/firm_lobfeat_test.cpp
    auto cut = f.rfind("/cpp/");
    return f.substr(0, cut) + "/data/";
}

static std::vector<std::vector<std::string>> read_csv(const std::string& path) {
    std::ifstream in(path);
    assert(in.good());
    std::vector<std::vector<std::string>> rows;
    std::string line;
    std::getline(in, line);                         // header
    while (std::getline(in, line)) {
        std::vector<std::string> cells;
        std::stringstream ss(line);
        std::string c;
        while (std::getline(ss, c, ',')) cells.push_back(c);
        rows.push_back(cells);
    }
    return rows;
}

int main() {
    const auto dir = data_dir();
    std::vector<double> g;
    for (const auto& r : read_csv(dir + "fixture_g.csv")) g.push_back(std::stod(r[1]));
    const auto msgs = read_csv(dir + "fixture_msgs.csv");
    const auto exp = read_csv(dir + "fixture_expected.csv");
    assert(msgs.size() == exp.size() && !msgs.empty());
    firm::LobFeatures eng(5, g);
    std::size_t checked = 0;
    for (std::size_t i = 0; i < msgs.size(); ++i) {
        const auto& m = msgs[i];
        auto f = eng.on(m[0][0], std::stoll(m[1]), std::stoi(m[2]), std::stoll(m[3]), std::stoll(m[4]));
        const auto& e = exp[i];
        if (e[0] == "nan") { assert(!f); continue; }
        assert(f);
        auto close = [](double a, const std::string& b) { return std::fabs(a - std::stod(b)) < 1e-12; };
        assert(f->bid == std::stoll(e[0]) && f->ask == std::stoll(e[1]));
        assert(f->bid_qty == std::stoll(e[2]) && f->ask_qty == std::stoll(e[3]));
        assert(close(f->imbalance, e[4]) && close(f->depth_imbalance, e[5]));
        assert(f->ofi == std::stoll(e[6]) && f->ofi_cum == std::stoll(e[7]));
        assert(close(f->wmid, e[8]) && close(f->micro, e[9]));
        ++checked;
    }
    assert(checked > 1000);
    std::printf("lobfeat C++: %zu rows match the Python reference\n", checked);
    return 0;
}
