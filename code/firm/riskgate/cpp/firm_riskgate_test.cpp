// firm.riskgate (C++20): the fixture's event stream replayed to the Python reference's decisions (the string, its
// FNV-1a hash and its counts in data/expected.txt); every check at its boundary; zero allocations while replaying.
#include "firm_riskgate.hpp"
#include "../../arena/cpp/firm_alloc_count.hpp"

#include <cstdio>
#include <fstream>
#include <map>
#include <sstream>
#include <string>
#include <vector>

using namespace firm::risk;

static const std::string D = "code/firm/riskgate/data/";

static std::string slurp(const std::string& p) {
    std::ifstream f(p);
    std::stringstream s;
    s << f.rdbuf();
    return s.str();
}

struct Ev {
    std::int64_t t = 0;
    char k = 0, side = 0, level = 0;
    int strat = -1, version = 0, idx = 0;
    std::uint32_t instr = 0;
    std::uint64_t cl = 0;
    std::int64_t qty = 0, price = 0;
    bool cancel = false;
};

static std::uint64_t fnv1a(const std::string& s) {
    std::uint64_t h = 0xcbf29ce484222325ULL;
    for (unsigned char c : s) h = (h ^ c) * 0x100000001b3ULL;
    return h;
}

int main() {
    int fails = 0;
    Names names;
    const auto j = firm::exchsim::json::parse(slurp(D + "limits.json"));
    std::map<int, Limits> lim;
    for (const auto& [k, v] : j.o) lim[std::stoi(k)] = parse_limits(v, names);

    // parse the events once, before timing or counting
    std::vector<Ev> ev;
    std::istringstream in(slurp(D + "events.txt"));
    std::string line;
    while (std::getline(in, line)) {
        std::istringstream l(line);
        Ev e;
        std::string k, a, b, c;
        l >> e.t >> k;
        e.k = k[0];
        if (e.k == 'L') l >> e.version;
        else if (e.k == 'P') l >> e.instr >> e.price;
        else if (e.k == 'O') {
            l >> e.cl >> a >> e.instr >> b >> e.qty >> e.price;
            e.strat = names.find(names.strat, a), e.side = b[0];
        } else if (e.k == 'F') l >> e.cl >> e.qty >> e.price;
        else if (e.k == 'X') l >> e.cl;
        else if (e.k == 'K' || e.k == 'U') {
            l >> a >> b >> c;
            e.level = a == "firm" ? 'F' : a == "desk" ? 'D' : 'S';
            e.idx = e.level == 'D' ? names.find(names.desk, b) : e.level == 'S' ? names.find(names.strat, b) : 0;
            e.cancel = c == "cancel";
        }
        ev.push_back(e);
    }
    Gate g(lim.at(1), ev.front().t);
    std::string out;
    out.reserve(ev.size());
    const auto a0 = firm::arena::allocations();
    std::size_t cancels = 0;
    for (const Ev& e : ev) {
        switch (e.k) {
            case 'L': g.set_limits(e.t, lim.at(e.version)); break;
            case 'H': g.heartbeat(e.t); break;
            case 'P': g.set_reference(e.t, e.instr, e.price); break;
            case 'O': out += g.check(e.t, e.strat, e.instr, e.side, e.qty, e.price, e.cl).code; break;
            case 'F': g.on_fill(e.cl, e.qty, e.price); break;
            case 'X': g.on_done(e.cl); break;
            case 'K': g.kill(e.level, e.idx, e.cancel, [&](std::uint64_t) { ++cancels; }); break;
            case 'U': g.unkill(e.level, e.idx); break;
        }
    }
    const auto allocs = firm::arena::allocations() - a0;
    const std::string exp = slurp(D + "expected.txt");
    const std::string head = exp.substr(0, exp.find('\n'));
    std::string want = exp.substr(exp.find('\n') + 1);
    want.pop_back();
    char h[32];
    std::snprintf(h, sizeof h, "%016llx", static_cast<unsigned long long>(fnv1a(out)));
    std::printf("%zu events, %zu decisions, hash %s, %zu cancels on kill, %llu allocations\n  %s\n", ev.size(),
                out.size(), h, cancels, allocs, head.c_str());
    if (out != want || head.find(h) == std::string::npos || allocs) {
        std::size_t i = 0;
        while (i < out.size() && i < want.size() && out[i] == want[i]) ++i;
        std::printf("FIRST DIFFERENCE at decision %zu\n", i), ++fails;
    }

    // boundaries: a fresh gate, one instrument, each limit exactly at and one past
    {
        Limits l = lim.at(1);
        Gate b(l, 0);
        b.set_reference(0, 1, 1'000'000);                 // collar 200 bp: [980,000, 1,020,000]
        const int s1 = 0;
        const Decision d[] = {b.check(1, s1, 1, 'B', 100, 1'020'000, 1), b.check(2, s1, 1, 'B', 100, 1'020'001, 2),
                              b.check(3, s1, 1, 'S', 100, 980'000, 3), b.check(4, s1, 1, 'S', 100, 979'999, 4),
                              b.check(5, s1, 1, 'B', 2'000, 1'000'000, 5), b.check(6, s1, 1, 'B', 2'001, 1'000'000, 6)};
        const std::string want_b = "..C.C.Q";
        std::string got = ".";
        for (const auto& x : d) got += x.code;
        if (got != want_b) std::printf("boundaries: %s, expected %s\n", got.c_str(), want_b.c_str()), ++fails;
        // fail closed: past max_age without a heartbeat, every order is refused as stale
        const Decision st = b.check(l.max_age + 10, s1, 1, 'B', 100, 1'000'000, 7);
        if (!(st.mask & (1u << Stale))) std::printf("stale limits not refused\n"), ++fails;
    }
    // Book 11's firm.riskctl exports its policy with a "riskgate" section in this schema: the gate runs on it
    {
        std::ifstream rf("code/firm/riskctl/data/limits.json");
        if (rf) {
            std::stringstream ss;
            ss << rf.rdbuf();
            // the file's "riskctl" section holds dollars as decimals, which the simulator's integer-only JSON
            // reader refuses: take the "riskgate" object alone (integers only), by matching its braces
            const std::string all = ss.str();
            std::size_t a0 = all.find('{', all.find("\"riskgate\"")), a1 = a0;
            for (int depth = 0; a1 < all.size(); ++a1) {
                depth += all[a1] == '{' ? 1 : all[a1] == '}' ? -1 : 0;
                if (depth == 0) break;
            }
            Names n3;
            const Limits l = parse_limits(firm::exchsim::json::parse(all.substr(a0, a1 - a0 + 1)), n3);
            Gate g(l, 0);
            g.set_reference(0, 1, 1'000'000);
            const int qa = n3.find(n3.strat, "quoter_a");
            const char a = g.check(1, qa, 1, 'B', 5'000, 1'000'000, 1).code;
            const char b = g.check(2, qa, 1, 'B', 5'001, 1'000'000, 2).code;
            std::printf("riskctl limits: %c %c\n", a, b);
            if (a != '.' || b != 'Q') ++fails;
        }
    }
    std::printf(fails ? "FAIL\n" : "ok\n");
    return fails ? 1 : 0;
}
