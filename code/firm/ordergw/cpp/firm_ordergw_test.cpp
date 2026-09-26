// firm.ordergw (C++20): the state table is the Python reference's (data/table.txt); both journals replay to the
// summaries in data/expected.txt, once from the journal's fields and once through encoded wire reports; every request
// is re-made with the journal's result; and replaying allocates nothing.
#include "firm_ordergw.hpp"
#include "../../arena/cpp/firm_alloc_count.hpp"

#include <cstdio>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

using namespace firm::ogw;

static const char* D = "code/firm/ordergw/data/";

struct Line {
    std::int64_t t = 0;
    char k = 0, sub = 0, side = 0, reason = ' ';
    std::uint64_t cl = 0, new_cl = 0;
    std::int64_t qty = 0, price = 0, leaves = 0;
    bool send = false;
};

static std::vector<Line> journal(const std::string& name) {
    std::ifstream f(std::string(D) + "journal_" + name + ".txt");
    std::vector<Line> out;
    std::string s;
    while (std::getline(f, s)) {
        std::istringstream in(s);
        Line l;
        std::string k, a, res;
        in >> l.t >> k;
        l.k = k[0];
        if (l.k == 'Q') {
            in >> a >> l.cl;
            l.sub = a[0];
            if (l.sub == 'N') in >> a >> l.qty >> l.price, l.side = a[0];
            else if (l.sub == 'U') in >> l.new_cl >> l.qty >> l.price;
            in >> res;
            l.send = res == "send";
        } else {
            std::string reason;
            in >> a >> l.cl >> l.qty >> l.price >> l.leaves >> reason >> l.new_cl;
            l.sub = a[0];
            l.reason = reason == "-" ? ' ' : reason[0];
        }
        out.push_back(l);
    }
    return out;
}

static std::size_t encode_report(const Line& l, std::uint8_t* b) {
    using namespace firm::wire;
    switch (l.sub) {
        case 'A': OutAWriter(b).cl_ord_id(l.cl); return OutA::kLength;
        case 'E':
            OutEWriter(b).cl_ord_id(l.cl).qty(static_cast<std::uint32_t>(l.qty)).leaves(static_cast<std::uint32_t>(l.leaves));
            return OutE::kLength;
        case 'C': OutCWriter(b).cl_ord_id(l.cl).reason(l.reason); return OutC::kLength;
        case 'U': OutUWriter(b).cl_ord_id(l.cl).new_cl_ord_id(l.new_cl); return OutU::kLength;
        default: OutJWriter(b).cl_ord_id(l.cl).reason(l.reason); return OutJ::kLength;
    }
}

// Replays one journal; wire=true feeds the reports as encoded messages. Returns the mismatches.
static int replay(const std::vector<Line>& j, Gateway& g, bool wire) {
    int bad = 0;
    std::uint8_t buf[64];
    for (const Line& l : j) {
        if (l.k == 'Q') {
            std::size_t n = 0;
            if (l.sub == 'N') n = g.new_order(l.t, l.cl, l.side, l.qty, l.price, buf);
            else if (l.sub == 'X') n = g.cancel(l.t, l.cl, buf);
            else n = g.replace(l.t, l.cl, l.new_cl, l.qty, l.price, buf);
            bad += (n > 0) != l.send;
        } else if (wire) {
            const std::size_t n = encode_report(l, buf);
            bad += !g.on_wire(buf, n);
        } else {
            bad += !g.on_report(l.sub, l.cl, l.qty, l.leaves, l.reason, l.new_cl);
        }
    }
    return bad;
}

static std::uint8_t state_of(const std::string& s) {
    for (std::uint8_t i = 0; i < NStates; ++i)
        if (s == kStateName[i]) return i;
    return X;
}

int main() {
    int fails = 0;
    // 1. the table
    const char* ev[] = {"ack", "reject", "fill", "fill_all", "cancel_req", "cancel_ack", "too_late", "replace_req",
                        "replace_ack"};
    std::ifstream tf(std::string(D) + "table.txt");
    std::string s, e, n;
    int allowed = 0, rows = 0;
    while (tf >> s >> e >> n) {
        ++rows;
        int k = 0;
        while (k < NEvents && e != ev[k]) ++k;
        if (k == NEvents || kTable[state_of(s)][k] != state_of(n)) {
            std::printf("table: %s %s should give %s\n", s.c_str(), e.c_str(), n.c_str());
            ++fails;
        }
    }
    for (auto& r : kTable)
        for (auto c : r) allowed += c != X;
    if (allowed != rows || rows == 0) std::printf("table: %d transitions here, %d in the reference\n", allowed, rows), ++fails;

    // 2. the journals, from fields and from the wire
    std::ifstream ef(std::string(D) + "expected.txt");
    std::string line;
    while (std::getline(ef, line)) {
        const std::string name = line.substr(0, line.find(' ')), want = line.substr(line.find(' ') + 1);
        const auto j = journal(name);
        const Limits lim = name == "replace" ? Limits{300, 2} : Limits{10'000, 100};
        for (bool wire : {false, true}) {
            Gateway g(lim);
            const auto a0 = firm::arena::allocations();
            const int bad = replay(j, g, wire);
            const auto allocs = firm::arena::allocations() - a0;
            const std::string got = g.summary();
            std::printf("%s%s: %zu lines, %d mismatches, %llu allocations\n  %s\n", name.c_str(),
                        wire ? " (wire)" : "", j.size(), bad, allocs, got.c_str());
            if (bad || allocs || got != want) std::printf("  expected %s\n", want.c_str()), ++fails;
        }
    }

    // 3. worst-case accounting refuses the order a naive count would send
    {
        Gateway g(Limits{1000, 50, 100, 100});
        std::uint8_t b[64];
        g.new_order(0, 1, 'B', 100, 1000, b);
        g.on_report('A', 1, 0, 0, ' ', 0);
        g.cancel(20, 1, b);
        const bool refused = g.new_order(21, 2, 'B', 100, 1000, b) == 0 && g.why() == Why::Exposure;
        if (!refused || g.worst_long() != 100) std::printf("worst-case accounting did not refuse\n"), ++fails;
        g.on_report('E', 1, 100, 0, ' ', 0);
        g.on_report('J', 1, 0, 0, 'L', 0);
        if (g.position() != 100 || g.races() != 1 || g.open_orders() != 0) std::printf("race not counted\n"), ++fails;
    }
    std::printf(fails ? "FAIL\n" : "ok\n");
    return fails ? 1 : 0;
}
