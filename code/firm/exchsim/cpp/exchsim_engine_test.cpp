// Replays data/fixture_journal.bin through the C++20 engine and compares its output log, byte for byte, with the
// Python engine's (data/fixture_out.bin); round-trips every golden message through the codec.
#include "exchsim_engine.hpp"

#include <cassert>
#include <cstdio>
#include <fstream>
#include <iterator>
#include <sstream>

using namespace firm::exchsim;

static std::string data_dir() {
    std::string f = __FILE__;
    return f.substr(0, f.rfind("/cpp/")) + "/data/";
}
static Bytes read(const std::string& path) {
    std::ifstream in(path, std::ios::binary);
    assert(in.good());
    return Bytes((std::istreambuf_iterator<char>(in)), std::istreambuf_iterator<char>());
}

template <class Dec>
static std::size_t round_trip(const std::string& file, Dec dec) {
    const Bytes b = read(data_dir() + "golden/" + file);
    std::size_t i = 0, n = 0;
    while (i < b.size()) {
        const std::size_t len = static_cast<std::size_t>(get(b, i, 2));
        const Span s(b.data() + i + 2, len);
        Bytes again;
        encode(again, dec(s));
        if (!std::equal(again.begin(), again.end(), s.begin(), s.end())) {
            std::printf("codec mismatch in %s at offset %zu\n", file.c_str(), i);
            std::exit(1);
        }
        i += 2 + len;
        ++n;
    }
    return n;
}

int main() {
    std::size_t n = round_trip("feed.bin", decode_feed) + round_trip("in.bin", decode_in) +
                    round_trip("out.bin", decode_out) + round_trip("ctl.bin", decode_ctl);
    std::printf("codec: %zu golden messages round-trip\n", n);

    std::ifstream cf(data_dir() + "fixture_config.json");
    std::stringstream ss;
    ss << cf.rdbuf();
    const std::string text = ss.str();
    Engine e(json::parse(text));
    const Bytes journal = read(data_dir() + "fixture_journal.bin");
    const Bytes want = read(data_dir() + "fixture_out.bin");
    Bytes out;
    u32 idx = 0;
    std::size_t feed_n = 0;
    for_each_record(journal, [&](const JournalRecord& r) {
        e.process(r.t_ns, r.session, r.payload);
        const std::size_t start = out.size();
        put(out, idx, 4);
        put(out, e.feed.size(), 2);
        put(out, e.reports.size(), 2);
        for (const auto& m : e.feed) { Bytes b; encode(b, m); put(out, b.size(), 2); out.insert(out.end(), b.begin(), b.end()); }
        for (const auto& [s, m] : e.reports) {
            Bytes b; encode(b, m);
            put(out, s, 2); put(out, b.size(), 2); out.insert(out.end(), b.begin(), b.end());
        }
        feed_n += e.feed.size();
        if (out.size() > want.size() || !std::equal(out.begin() + static_cast<long>(start), out.end(),
                                                    want.begin() + static_cast<long>(start))) {
            std::printf("first difference at journal record %u\n", idx);
            std::exit(1);
        }
        ++idx;
    });
    for (u16 loc : e.locates()) {
        const auto snap = e.snapshot(loc, feed_n, e.ts);
        put(out, 0xFFFFFFFFu, 4);
        put(out, loc, 2);
        put(out, snap.size(), 2);
        for (const auto& m : snap) { Bytes b; encode(b, m); put(out, b.size(), 2); out.insert(out.end(), b.begin(), b.end()); }
    }
    if (out != want) { std::printf("snapshots differ (%zu vs %zu bytes)\n", out.size(), want.size()); return 1; }
    std::printf("engine: %u journal records, %zu executions, output byte-identical to Python (%zu bytes)\n", idx,
                e.trades.size(), out.size());
    return 0;
}
