// firm.feedhandler (C++20): the three runs of the fixture -- clean, impaired with retransmission, impaired with
// snapshot recovery -- give the Python reference's event counts, hashes, staleness and counters.
#include "firm_feedhandler.hpp"
#include "../../ring/cpp/firm_ring.hpp"

#include <cstdio>
#include <fstream>
#include <iterator>
#include <sstream>
#include <string>

using namespace firm::feed2;

static std::vector<std::uint8_t> file(const char* name) {
    std::ifstream f(std::string("code/firm/feedhandler/data/") + name, std::ios::binary);
    return {std::istreambuf_iterator<char>(f), {}};
}

static std::string summary(const Handler& h) {
    std::uint64_t stale_ns = 0;
    for (const auto& [s, e] : h.stale) stale_ns += e - s;
    char hex[17];
    std::snprintf(hex, sizeof hex, "%016llx", static_cast<unsigned long long>(h.hash));
    std::ostringstream o;
    o << h.events << ' ' << hex << ' ' << h.stale.size() << ' ' << stale_ns << ' ' << h.c.packets << ' ' << h.c.duplicates
      << ' ' << h.c.gaps << ' ' << h.c.filled_by_line << ' ' << h.c.retransmissions << ' ' << h.c.snapshots;
    return o.str();
}

int main() {
    const auto fa = file("lineA.bin"), fb = file("lineB.bin"), fc = file("clean.bin"), fs = file("snapshot.bin");
    const auto a = recorded(fa), b = recorded(fb), clean = recorded(fc), snap = recorded(fs);
    std::ifstream ex("code/firm/feedhandler/data/expected.txt");
    std::string line;
    std::getline(ex, line);
    int fails = 0;
    const RetxServer server(clean, 100'000);
    for (const char* run : {"clean", "retx", "snapshot"}) {
        std::getline(ex, line);
        Handler h(std::string(run) == "retx" ? &server : nullptr);
        if (std::string(run) == "clean") h.run(clean, {}, {});
        else h.run(a, b, snap);
        const std::string got = std::string(run) + " " + summary(h);
        if (got != line) {
            ++fails;
            std::printf("%s\n  got  %s\n  want %s\n", run, got.c_str(), line.c_str());
        }
    }
    // Publication on the firm's ring: every event of the retransmission run through an SPSC ring of 64-byte slots,
    // read back in order and hashed again.
    std::vector<std::uint8_t> region(firm::ring::region_size(4096, 64));
    firm::ring::format(region.data(), 4096, 64);
    firm::ring::Spsc out(region.data()), in(region.data());
    Handler h(&server);
    std::uint64_t written = 0;
    h.on_event = [&](const Event& e) { written += out.try_write(&e, sizeof e) ? 1 : 0; };
    h.run(a, b, snap);
    std::uint64_t rehash = 0xCBF29CE484222325ULL, read = 0;
    Event e;
    while (in.try_read(&e, sizeof e) == static_cast<int>(sizeof e)) {
        rehash = fnv1a(e, rehash);
        ++read;
    }
    if (written != h.events || read != h.events || rehash != h.hash) {
        ++fails;
        std::printf("ring: wrote %llu, read %llu of %llu\n", static_cast<unsigned long long>(written),
                    static_cast<unsigned long long>(read), static_cast<unsigned long long>(h.events));
    }
    std::printf("%s\n", fails ? "FAILED" : "clean, retransmission and snapshot runs match the reference; ring ok");
    return fails ? 1 : 0;
}
