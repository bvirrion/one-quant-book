// Replays the shared fixture's shadow orders through the C++ 'fifo' core and compares every fill with Python's.
#include "firm_lobreplay.hpp"

#include <cassert>
#include <cstdio>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

static std::string data_dir() {
    std::string f = __FILE__;                       // .../code/firm/lobreplay/cpp/firm_lobreplay_test.cpp
    return f.substr(0, f.rfind("/cpp/")) + "/data/";
}

static std::vector<std::vector<std::string>> read_csv(const std::string& path) {
    std::ifstream in(path);
    assert(in.good());
    std::vector<std::vector<std::string>> rows;
    std::string line;
    std::getline(in, line);
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
    std::vector<firm::Msg> msgs;
    for (const auto& r : read_csv(data_dir() + "fixture_msgs.csv"))
        msgs.push_back({std::stod(r[0]), r[1][0], std::stol(r[2]), std::stoi(r[3]), std::stol(r[4]), std::stol(r[5])});
    std::vector<firm::VOrder> orders;
    for (const auto& r : read_csv(data_dir() + "fixture_orders.csv"))
        orders.push_back({std::stoi(r[0]), std::stoi(r[1]), std::stol(r[2]), std::stol(r[3]), std::stod(r[4]), std::stod(r[5])});
    auto got = firm::track_fifo(msgs, orders);
    auto want = read_csv(data_dir() + "fixture_fills.csv");
    assert(got.size() == want.size());
    for (size_t i = 0; i < got.size(); ++i) {
        assert(got[i].vid == std::stoi(want[i][0]));
        assert(got[i].t == std::stod(want[i][1]));
        assert(got[i].qty == std::stol(want[i][2]));
    }
    std::printf("firm_lobreplay C++: %zu messages, %zu orders, %zu fills match\n", msgs.size(), orders.size(), got.size());
    return 0;
}
