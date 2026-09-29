// Reproduces the Python reference's counters and hashes on the shared fixture (data/events.txt, data/expected.txt).
#include <cstdio>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

#include "firm_nicring.hpp"

struct Ev { char kind; std::uint64_t a; std::uint32_t b; };

int main() {
    const std::string here = __FILE__;
    const std::string dir = here.substr(0, here.rfind('/') + 1) + "../data/";
    std::ifstream in(dir + "events.txt"), ex(dir + "expected.txt");
    if (!in || !ex) { std::puts("missing fixture"); return 1; }
    std::vector<Ev> ev;
    std::string line;
    while (std::getline(in, line)) {
        std::istringstream s(line);
        Ev e{};
        s >> e.kind >> e.a;
        if (e.kind == 'N') s >> e.b;
        ev.push_back(e);
    }
    int bad = 0, n = 0;
    while (std::getline(ex, line)) {
        if (line.empty() || line[0] == '#') continue;
        std::istringstream s(line);
        unsigned size = 0, refill = 0;
        unsigned long long rx, drops, processed, doorbells, max_owned;
        std::string hash;
        s >> size >> refill >> rx >> drops >> processed >> doorbells >> max_owned >> hash;
        firm::nicring::Ring r(size, refill);
        for (const Ev& e : ev) {
            if (e.kind == 'N') r.nic_rx(e.a, e.b); else r.poll(static_cast<std::uint32_t>(e.a));
            r.note_owned();
        }
        char h[17];
        std::snprintf(h, sizeof h, "%016llx", static_cast<unsigned long long>(r.hash));
        const bool ok = r.rx == rx && r.drops == drops && r.processed == processed && r.doorbells == doorbells &&
                        r.max_owned == max_owned && hash == h;
        if (!ok) { std::printf("mismatch for size %u refill %u\n", size, refill); ++bad; }
        ++n;
    }
    std::printf("nicring: %d configurations, %d mismatches\n", n, bad);
    return bad == 0 && n > 0 ? 0 : 1;
}
