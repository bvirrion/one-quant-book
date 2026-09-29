// Reads data/fixture.pcap and reproduces the Python reader's summary in data/fixture_expected.txt: record count,
// total bytes, first and last timestamps, FNV-1a over every frame's bytes in order.
#include <cstdio>
#include <fstream>
#include <iterator>
#include <string>
#include <vector>

#include "firm_wirecap.hpp"

int main() {
    const std::string here = __FILE__;
    const std::string dir = here.substr(0, here.rfind('/') + 1) + "../data/";
    std::ifstream in(dir + "fixture.pcap", std::ios::binary);
    std::ifstream ex(dir + "fixture_expected.txt");
    if (!in || !ex) { std::puts("missing fixture"); return 1; }
    const std::vector<std::uint8_t> file((std::istreambuf_iterator<char>(in)), std::istreambuf_iterator<char>());
    unsigned long long bytes = 0, first = 0, last = 0, h = 0xCBF29CE484222325ULL;
    const long n = firm::wirecap::for_each_record(file, [&](const firm::wirecap::Record& r) {
        if (bytes == 0) first = r.t_ns;
        last = r.t_ns;
        bytes += r.frame.size();
        for (auto b : r.frame) h = (h ^ b) * 0x100000001B3ULL;
    });
    long en = 0;
    unsigned long long eb = 0, ef = 0, el = 0;
    char eh[32] = {};
    std::string line;
    std::getline(ex, line);
    std::sscanf(line.c_str(), "%ld %llu %llu %llu %31s", &en, &eb, &ef, &el, eh);
    char got[32];
    std::snprintf(got, sizeof got, "%016llx", h);
    const bool ok = n == en && bytes == eb && first == ef && last == el && std::string(got) == eh;
    std::printf("wirecap reader: %ld records, %llu bytes, %s\n", n, bytes, ok ? "identical to the Python reader" : "MISMATCH");
    return ok ? 0 : 1;
}
