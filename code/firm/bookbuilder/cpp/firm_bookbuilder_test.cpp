// firm.bookbuilder (C++20): the ladder book gives the Python reference's level 2 after every event of both fixtures
// (large-tick simulator events, synthetic small-tick events), keeps its invariants, and allocates nothing per event.
#include "firm_bookbuilder.hpp"
#include "../../arena/cpp/firm_alloc_count.hpp"

#include <cstdio>
#include <fstream>
#include <iterator>
#include <sstream>

using namespace firm::book;

static std::vector<Event> events(const std::string& name) {
    std::ifstream f("code/firm/bookbuilder/data/" + name + ".bin", std::ios::binary);
    const std::vector<std::uint8_t> b{std::istreambuf_iterator<char>(f), {}};
    std::vector<Event> out;
    for (std::size_t i = 0; i + 48 <= b.size(); i += 48) {
        Event e;
        e.kind = b[i];
        e.side = b[i + 1];
        std::memcpy(&e.locate, &b[i + 2], 2);
        std::memcpy(&e.seq, &b[i + 4], 8);
        std::memcpy(&e.ts, &b[i + 12], 8);
        std::memcpy(&e.ref, &b[i + 20], 8);
        std::memcpy(&e.ref2, &b[i + 28], 8);
        std::memcpy(&e.price, &b[i + 36], 4);
        std::memcpy(&e.qty, &b[i + 40], 8);
        out.push_back(e);
    }
    return out;
}

int main() {
    std::ifstream ex("code/firm/bookbuilder/data/expected.txt");
    int fails = 0;
    for (std::string line; std::getline(ex, line);) {
        std::istringstream in(line);
        std::string name, hash;
        std::size_t n;
        in >> name >> n >> hash;
        const auto ev = events(name);
        const std::uint32_t tick = name == "events_sim" ? 100 : 1;
        LadderBook book(tick);
        std::uint64_t h = 0xCBF29CE484222325ULL;
        const auto a0 = firm::arena::allocations();
        for (const auto& e : ev) {
            book.apply(e);
            h = l2_hash(book, h);
        }
        const auto allocs = firm::arena::allocations() - a0;
        char got[17];
        std::snprintf(got, sizeof got, "%016llx", static_cast<unsigned long long>(h));
        LadderBook checked(tick);
        std::string err;
        for (const auto& e : ev) {
            checked.apply(e);
            if (!checked.stale && err.empty()) err = checked.check();
        }
        std::printf("%s: %zu events, hash %s (want %s), %llu allocations, %llu recentrings, invariants %s\n",
                    name.c_str(), ev.size(), got, hash.c_str(), static_cast<unsigned long long>(allocs),
                    static_cast<unsigned long long>(book.recentrings), err.empty() ? "ok" : err.c_str());
        if (ev.size() != n || hash != got || allocs != 0 || !err.empty()) ++fails;
    }
    // A narrow ladder on the small-tick fixture recentres, spills into the sparse map, and still agrees.
    {
        const auto ev = events("events_small");
        LadderBook narrow(1, 256), wide(1, 1 << 14);
        std::uint64_t h1 = 0xCBF29CE484222325ULL, h2 = h1;
        for (const auto& e : ev) {
            narrow.apply(e);
            wide.apply(e);
            h1 = l2_hash(narrow, h1);
            h2 = l2_hash(wide, h2);
        }
        std::printf("narrow ladder: %llu recentrings, same level 2: %s\n",
                    static_cast<unsigned long long>(narrow.recentrings), h1 == h2 ? "yes" : "no");
        if (h1 != h2 || narrow.recentrings == 0) ++fails;
    }
    // The order map: insert, find, erase with backward shift, on colliding keys.
    {
        OrderMap m(16);
        for (std::uint64_t k = 1; k <= 10; ++k) m.insert(k * 1024, static_cast<std::uint32_t>(k));
        m.erase(3 * 1024);
        m.erase(1 * 1024);
        bool ok = !m.find(1024) && !m.find(3 * 1024);
        for (std::uint64_t k : {2, 4, 5, 6, 7, 8, 9, 10}) ok = ok && m.find(k * 1024) && *m.find(k * 1024) == k;
        if (!ok) { ++fails; std::printf("order map failed\n"); }
    }
    std::printf("%s\n", fails ? "FAILED" : "ok");
    return fails ? 1 : 0;
}
