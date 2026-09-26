// Replays the shared fixture through the C++20 book and compares every level-2 snapshot with Python's.
#include "firm_lob.hpp"

#include <cassert>
#include <cstdio>
#include <fstream>
#include <sstream>
#include <string>

static std::string data_dir() {
    std::string f = __FILE__;
    return f.substr(0, f.rfind("/cpp/")) + "/data/";
}

int main() {
    std::ifstream msgs(data_dir() + "fixture_msgs.csv"), expect(data_dir() + "fixture_l2.txt");
    assert(msgs.good() && expect.good());
    std::string line, header, b_line, s_line;
    std::getline(msgs, line);
    firm::lob::MessageBook book;
    std::size_t i = 0, checked = 0;
    std::getline(expect, header);
    while (std::getline(msgs, line)) {
        std::stringstream ss(line);
        std::string kind, oid, side, price, qty;
        std::getline(ss, kind, ',');
        std::getline(ss, oid, ',');
        std::getline(ss, side, ',');
        std::getline(ss, price, ',');
        std::getline(ss, qty, ',');
        const auto ref = std::stoull(oid);
        if (kind == "A") book.add(ref, std::stoi(side), std::stoll(price), std::stoll(qty));
        else book.reduce(ref, std::stoll(qty));
        ++i;
        if (!header.empty() && header == "# " + std::to_string(i)) {
            std::getline(expect, b_line);
            std::getline(expect, s_line);
            if (firm::lob::l2_lines(book, 5) != b_line + "\n" + s_line) {
                std::printf("mismatch after message %zu\n", i);
                return 1;
            }
            ++checked;
            if (!std::getline(expect, header)) header.clear();
        }
    }
    assert(checked == 147);
    std::printf("firm_lob C++: %zu messages, %zu level-2 snapshots identical\n", i, checked);
    return 0;
}
