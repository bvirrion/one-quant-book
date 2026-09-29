// Acceptance test of firm.tickstore, C++ side: the per-instrument summary of both fixture versions, exactly.
#include "firm_tickstore.hpp"

#include <cstdio>
#include <fstream>
#include <sstream>
#include <string>

int main() {
    const std::string dir = "code/firm/tickstore/data/";
    std::ifstream ex(dir + "fixture_expected.txt");
    std::string name, line;
    int checked = 0;
    while (std::getline(ex, line)) {           // file locate count executed last_seq
        std::istringstream is(line);
        unsigned loc = 0;
        unsigned long long c = 0, q = 0, s = 0;
        is >> name >> loc >> c >> q >> s;
        firm::tickstore::FlatFile f(dir + name);
        const auto sum = firm::tickstore::summarise(f);
        const auto it = sum.find(static_cast<std::uint16_t>(loc));
        if (it == sum.end() || it->second.count != c || it->second.executed != q || it->second.last_seq != s) {
            std::printf("mismatch %s locate %u\n", name.c_str(), loc);
            return 1;
        }
        ++checked;
    }
    if (checked < 4) { std::puts("fixture too small"); return 1; }
    std::printf("ok %d rows\n", checked);
    return 0;
}
