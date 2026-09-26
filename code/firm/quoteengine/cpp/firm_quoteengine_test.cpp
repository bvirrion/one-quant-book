// Replays the shared fixture and compares every action with the Python reference's log.
#include "firm_quoteengine.hpp"

#include <cassert>
#include <cstdio>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

static std::string data_dir() {
    std::string f = __FILE__;
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
        if (!line.empty() && line.back() == ',') cells.emplace_back();
        rows.push_back(cells);
    }
    return rows;
}

int main() {
    const auto dir = data_dir();
    const auto par = read_csv(dir + "fixture_params.csv");
    firm::QuoteEngine e(std::stoi(par[0][0]), std::stoll(par[0][1]), std::stod(par[0][2]), std::stod(par[0][3]));
    std::vector<std::string> got;
    for (const auto& r : read_csv(dir + "fixture_events.csv")) {
        const auto& kind = r[1];
        if (kind == "U") {
            std::vector<std::pair<std::int64_t, std::int64_t>> tg;
            std::stringstream ss(r[4]);
            std::string item;
            while (std::getline(ss, item, '|')) {
                if (item.empty()) continue;
                const auto c = item.find(':');
                tg.emplace_back(std::stoll(item.substr(0, c)), std::stoll(item.substr(c + 1)));
            }
            for (const auto& a : e.update(std::stod(r[2]), std::stoi(r[3]), tg)) got.push_back(r[0] + "," + a.str());
        } else if (kind == "A") {
            e.ack(std::stoi(r[5]));
        } else {
            e.fill(std::stoi(r[5]), std::stoll(r[6]));
        }
    }
    std::ifstream in(dir + "fixture_expected.csv");
    std::string line;
    std::getline(in, line);
    std::size_t i = 0;
    while (std::getline(in, line)) {
        assert(i < got.size() && got[i] == line);
        ++i;
    }
    assert(i == got.size() && i > 1000);
    std::printf("quoteengine C++: %zu actions match the Python reference\n", i);
    return 0;
}
