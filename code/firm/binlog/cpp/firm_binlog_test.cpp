// firm.binlog (C++20): the sample statements logged through the ring and drained give data/sample.blog byte for byte
// (the Python reference's encoding); the writer thread writes the same bytes to a file; logging allocates nothing and
// a full ring drops and counts instead of waiting; and a day journaled and replayed through firm.stratengine gives the
// committed output hash.
#include "firm_binlog.hpp"
#include "../../arena/cpp/firm_alloc_count.hpp"
#include "../../stratengine/cpp/firm_stratengine.hpp"

#include <cstdio>
#include <fstream>
#include <iterator>
#include <string>
#include <string_view>
#include <vector>

using namespace firm::binlog;

static std::vector<std::uint8_t> slurp(const std::string& p) {
    std::ifstream f(p, std::ios::binary);
    return {std::istreambuf_iterator<char>(f), {}};
}

// The statements of make_binlog_fixtures.py, with argument types that give the same type codes.
static void sample(Logger& log) {
    log.log<"engine start v{}">(1000, std::uint32_t{1});
    for (int k = 0; k < 5; ++k) {
        const std::uint64_t t = 34'200'000'000'000ULL + 1000ULL * static_cast<std::uint64_t>(k);
        log.log<"{} {} at {} x {}">(t, "BS"[k % 2], k > 1 ? 'R' : 'N', std::int64_t{999'900 + 100 * k},
                                    std::uint32_t(100 * (k + 1)));
        log.log<"fill {} of {} at {}, position {}">(t + 10, std::uint64_t(40 + k), std::int64_t{100},
                                                    std::int64_t{999'900 - 100 * k}, std::int64_t{(k - 2) * 100});
        log.log<"{} half-spread {} ticks, skew {}">(t + 20, std::string_view("SIM1"), 2.5 + k / 4.0, -k);
    }
    log.log<"pulled">(34'200'000'009'000ULL);
}

int main() {
    int fails = 0;
    const auto want = slurp("code/firm/binlog/data/sample.blog");

    // 1. through the ring, drained in the same thread
    {
        Logger log;
        sample(log);
        std::vector<std::uint8_t> out = header();
        log.drain(out);
        if (out != want) std::printf("ring: %zu bytes, expected %zu\n", out.size(), want.size()), ++fails;
    }
    // 2. through the writer thread, into a file
    {
        const std::string path = "code/firm/binlog/cpp/bin/sample_test.blog";
        Logger log;
        {
            Writer w(log, path);
            sample(log);
        }
        if (slurp(path) != want) std::printf("writer: file differs from the fixture\n"), ++fails;
        std::remove(path.c_str());
    }
    // 3. no allocation while logging; a full ring drops and counts
    {
        Logger log(1024);
        const auto a0 = firm::arena::allocations();
        int ok = 0;
        for (int i = 0; i < 1500; ++i) ok += log.log<"fill {} of {} at {}, position {}">(
            static_cast<std::uint64_t>(i), std::uint64_t(40), std::int64_t{100}, std::int64_t{999'900},
            std::int64_t{i});
        const auto allocs = firm::arena::allocations() - a0;
        std::printf("1500 calls into a ring of 1024: %d written, %llu dropped, %llu allocations\n", ok,
                    static_cast<unsigned long long>(log.dropped()), allocs);
        if (allocs || ok != 1024 || log.dropped() != 476) ++fails;
    }
    // 4. journal a day's inputs, replay them through the strategy engine
    {
        const auto ev = slurp("code/firm/bookbuilder/data/events_small.bin");
        Journal j;
        std::vector<firm::strat::Event> live;
        for (std::size_t i = 0; i + 48 <= ev.size(); i += 48) {
            firm::strat::Event e;
            e.kind = ev[i];
            e.side = ev[i + 1];
            std::memcpy(&e.seq, &ev[i + 4], 8);
            std::memcpy(&e.ts, &ev[i + 12], 8);
            std::memcpy(&e.ref, &ev[i + 20], 8);
            std::memcpy(&e.ref2, &ev[i + 28], 8);
            std::memcpy(&e.price, &ev[i + 36], 4);
            std::memcpy(&e.qty, &ev[i + 40], 8);
            live.push_back(e);
            j.add(e.ts + 5'000, &ev[i]);        // received 5 us after the exchange's time stamp
        }
        std::vector<firm::strat::Event> replayed;
        for (const auto& [recv, b] : Journal::records(j.bytes)) {
            firm::strat::Event e;
            e.kind = b[0];
            e.side = b[1];
            std::memcpy(&e.seq, b + 4, 8);
            std::memcpy(&e.ts, b + 12, 8);
            std::memcpy(&e.ref, b + 20, 8);
            std::memcpy(&e.ref2, b + 28, 8);
            std::memcpy(&e.price, b + 36, 4);
            std::memcpy(&e.qty, b + 40, 8);
            replayed.push_back(e);
            (void)recv;
        }
        firm::strat::Engine<> a(1, firm::strat::Params{}), b(1, firm::strat::Params{});
        a.run(live);
        b.run(replayed);
        const auto exp = slurp("code/firm/stratengine/data/expected.txt");
        char h[17];
        std::snprintf(h, sizeof h, "%016llx", static_cast<unsigned long long>(b.hash));
        std::printf("journal: %zu records, %zu bytes; replay hash %s\n", replayed.size(), j.bytes.size(), h);
        if (a.hash != b.hash || std::string(exp.begin(), exp.begin() + 16) != h) ++fails;
    }
    std::printf(fails ? "FAIL\n" : "ok\n");
    return fails ? 1 : 0;
}
