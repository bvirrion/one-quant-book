// Chapter 23: find where two replays part. The strategy engine replays the same journaled events twice; the second
// run has a planted difference (its parameters change at event 3,000, as a value read from outside the journal
// would). Both runs log their actions through firm.binlog; comparing the two logs record by record finds the first
// action that differs, which must come at or after the planted event, and nothing before it may differ.
#include "../../../firm/binlog/cpp/firm_binlog.hpp"
#include "../../../firm/stratengine/cpp/firm_stratengine.hpp"

#include <cstdio>
#include <fstream>
#include <iterator>
#include <vector>

using namespace firm;

static std::vector<strat::Event> events() {
    std::ifstream f("code/firm/bookbuilder/data/events_small.bin", std::ios::binary);
    const std::vector<std::uint8_t> b{std::istreambuf_iterator<char>(f), {}};
    std::vector<strat::Event> out;
    for (std::size_t i = 0; i + 48 <= b.size(); i += 48) {
        strat::Event e;
        e.kind = b[i];
        e.side = b[i + 1];
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

// One run, its actions logged as binary records; returns the drained records.
static std::vector<std::uint8_t> run(const std::vector<strat::Event>& ev, const std::vector<strat::Snapshot>& ch) {
    strat::Engine<> eng(1, strat::Params{});
    eng.run(ev, ch);
    binlog::Logger log(1 << 16);
    std::vector<std::uint8_t> out;
    for (const auto& a : eng.actions) {
        log.log<"{} {} at {} x {} id {}">(a.t, a.kind, a.side, std::uint64_t{a.price}, std::uint64_t{a.qty}, a.id);
        if (out.size() % 4096 == 0) log.drain(out);
    }
    log.drain(out);
    return out;
}

int main() {
    const auto ev = events();
    const auto a = run(ev, {}), b = run(ev, {});
    strat::Params p;
    p.version = 2, p.half_spread_ticks = 3;
    const std::uint64_t planted = ev[3000].ts;
    const auto c = run(ev, {strat::Snapshot{planted, p}});
    // records have one size here (one statement): compare them in order
    const std::size_t rec = 16 + 1 + 1 + 8 + 8 + 8;
    auto first_diff = [&](const std::vector<std::uint8_t>& x, const std::vector<std::uint8_t>& y) {
        for (std::size_t k = 0; k * rec < std::min(x.size(), y.size()); ++k)
            if (std::memcmp(&x[k * rec], &y[k * rec], rec) != 0) return static_cast<long>(k);
        return x.size() == y.size() ? -1L : static_cast<long>(std::min(x.size(), y.size()) / rec);
    };
    const long same = first_diff(a, b), k = first_diff(a, c);
    std::uint64_t t = 0;
    if (k >= 0) std::memcpy(&t, &a[static_cast<std::size_t>(k) * rec + 8], 8);
    std::printf("%zu records; identical replays differ at %ld; planted change at t=%llu, first differing record %ld "
                "at t=%llu\n", a.size() / rec, same, static_cast<unsigned long long>(planted), k,
                static_cast<unsigned long long>(t));
    // the chapter quotes these two numbers
    const bool ok = same == -1 && k == 540 && a.size() / rec == 1084 && t >= planted;
    std::printf(ok ? "ok\n" : "FAIL\n");
    return ok ? 0 : 1;
}
