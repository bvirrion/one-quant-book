// The C++20 cycle model on the shared fixture: data/packets.bin cut into beats with two idle cycles between packets,
// run with each of data/expected.txt's settings; orders, rejects, first cycle and digest must match the Python model.
#include <cstdio>
#include <fstream>
#include <iterator>
#include <sstream>
#include <string>
#include <vector>

#include "firm_hwtrade.hpp"

int main() {
    const std::string here = __FILE__;
    const std::string dir = here.substr(0, here.rfind('/') + 1) + "../data/";
    std::ifstream pin(dir + "packets.bin", std::ios::binary), ex(dir + "expected.txt");
    if (!pin || !ex) { std::puts("missing fixture"); return 1; }
    const std::vector<unsigned char> b((std::istreambuf_iterator<char>(pin)), std::istreambuf_iterator<char>());
    std::vector<std::optional<firm::hwtrade::Beat>> beats;
    for (std::size_t off = 0; off + 4 <= b.size();) {
        const std::size_t n = (std::size_t(b[off]) << 24) | (b[off + 1] << 16) | (b[off + 2] << 8) | b[off + 3];
        off += 4;
        for (std::size_t i = 0; i < n; i += 8) {
            std::uint64_t d = 0;
            std::uint8_t keep = 0;
            for (std::size_t k = 0; k < 8; ++k) {
                d <<= 8;
                if (i + k < n) d |= b[off + i + k], keep |= static_cast<std::uint8_t>(0x80 >> k);
            }
            beats.push_back(firm::hwtrade::Beat{i + 8 >= n, keep, d});
        }
        beats.push_back(std::nullopt), beats.push_back(std::nullopt);
        off += n;
    }
    std::string line;
    int bad = 0, runs = 0;
    while (std::getline(ex, line)) {
        if (line.empty() || line[0] == '#') continue;
        std::istringstream s(line);
        unsigned long thresh, maxq, n_orders, rejects, digest;
        long kill, first;
        s >> thresh >> maxq >> kill >> n_orders >> rejects >> first >> digest;
        firm::hwtrade::Model m(1, 4, 64);
        const long total = static_cast<long>(beats.size()) + 8;
        for (long c = 0; c < total; ++c)
            m.step(c, c < static_cast<long>(beats.size()) ? beats[c] : std::nullopt, static_cast<std::uint32_t>(thresh),
                   static_cast<std::uint32_t>(maxq), kill >= 0 && c >= kill);
        unsigned long long dg = 0;
        for (std::size_t i = 0; i < m.orders.size(); ++i) {
            const auto& o = m.orders[i];
            dg = (dg + (i + 1) * (static_cast<unsigned long long>(o.cycle) * 7 + o.qty * 13ULL + o.price)) % (1ULL << 61);
        }
        const long f = m.orders.empty() ? -1 : m.orders[0].cycle;
        if (m.orders.size() != n_orders || m.rejects != rejects || f != first || dg != digest) {
            std::printf("mismatch at %s\n", line.c_str());
            ++bad;
        }
        ++runs;
    }
    std::printf("hwtrade cycle model: %d settings, %d mismatches\n", runs, bad);
    return bad == 0 && runs > 0 ? 0 : 1;
}
