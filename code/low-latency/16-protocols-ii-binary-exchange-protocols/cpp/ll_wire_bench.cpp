// Chapter 16 benchmark. Arguments: lineA.bin lineB.bin (recorded files).
//   Decoding the add, execute, cancel, delete and hidden-trade messages of line A: Book 1's decoder (copies into a
//   struct, one std::function call per message), the generated big-endian flyweights, and the SBE-style
//   little-endian flyweights; then every packet of line A through the MoldUDP64 framing and the dispatcher; then
//   the arbitration of both lines. Output: "decode,<method>,<ns per message>" and "arb,<counts...>,<ns per packet>".
#include <cstdio>
#include <fstream>
#include <iterator>
#include <string>
#include <vector>

#include "firm_feed.hpp"
#include "firm_ubench.hpp"
#include "firm_wirecodec_bridge.hpp"
#include "ll_arb.hpp"

using namespace firm::ubench;

static std::vector<std::uint8_t> file(const char* path) {
    std::ifstream f(path, std::ios::binary);
    return {std::istreambuf_iterator<char>(f), {}};
}

template <class F>
static double per_item(const Clock& clk, std::size_t items, F&& f, int reps = 21) {
    std::vector<double> t;
    for (int r = 0; r < reps + 2; ++r) {
        const std::uint64_t a = tsc_start();
        f();
        const std::uint64_t b = rdtscp();
        if (r >= 2) t.push_back(clk.ns(b - a) / static_cast<double>(items));
    }
    return quantile(t, 0.5);
}

int main(int argc, char** argv) {
    if (argc < 3) return 1;
    const Clock clk = Clock::calibrate();
    const auto fa = file(argv[1]), fb = file(argv[2]);
    const auto a = ll::arb::read_recorded(fa), b = ll::arb::read_recorded(fb);

    // Book 1's framing: u16 length | message, for the five message types Book 1 knows; and the same in SBE layout.
    std::vector<std::uint8_t> be, le;
    std::size_t n = 0, all = 0;
    for (const auto& k : a)
        firm::wire::for_each_block(k.p, k.n, [&](const std::uint8_t* m, std::size_t len) {
            ++all;
            if (firm::feed::expected_length(static_cast<char>(m[0])) != len) return;
            be.push_back(static_cast<std::uint8_t>(len >> 8));
            be.push_back(static_cast<std::uint8_t>(len));
            be.insert(be.end(), m, m + len);
            std::uint8_t out[128];
            const std::size_t k2 = firm::wire::to_sbe(m, len, out);
            le.push_back(static_cast<std::uint8_t>(k2 >> 8));
            le.push_back(static_cast<std::uint8_t>(k2));
            le.insert(le.end(), out, out + k2);
            ++n;
        });

    std::uint64_t sink = 0;
    const double book1 = per_item(clk, n, [&] {
        firm::feed::decode(std::span<const std::uint8_t>(be), [&](const firm::feed::Msg& m) { sink += m.shares + m.price; });
    });
    const double flyweight = per_item(clk, n, [&] {
        for (std::size_t i = 0; i < be.size();) {
            const std::size_t len = firm::wire::be16(be.data() + i);
            firm::wire::dispatch_feed(be.data() + i + 2, len, [&](auto m) {
                if constexpr (requires { m.shares(); }) sink += m.shares();
                if constexpr (requires { m.price(); }) sink += m.price();
            });
            i += 2 + len;
        }
    });
    const double sbe = per_item(clk, n, [&] {
        for (std::size_t i = 0; i < le.size();) {
            const std::size_t len = firm::wire::be16(le.data() + i);
            const std::uint8_t* p = le.data() + i + 2;
            const std::uint8_t* body = p + firm::sbe::kHeader;
            switch (firm::sbe::Header{p}.template_id()) {
                case firm::sbe::FeedA::kTemplateId: sink += firm::sbe::FeedA{body}.shares() + firm::sbe::FeedA{body}.price(); break;
                case firm::sbe::FeedE::kTemplateId: sink += firm::sbe::FeedE{body}.shares(); break;
                case firm::sbe::FeedX::kTemplateId: sink += firm::sbe::FeedX{body}.shares(); break;
                case firm::sbe::FeedD::kTemplateId: sink += firm::sbe::FeedD{body}.ref(); break;
                case firm::sbe::FeedP::kTemplateId: sink += firm::sbe::FeedP{body}.shares() + firm::sbe::FeedP{body}.price(); break;
                default: break;
            }
            i += 2 + len;
        }
    });
    const double packets = per_item(clk, all, [&] {
        for (const auto& k : a)
            firm::wire::for_each_block(k.p, k.n, [&](const std::uint8_t* m, std::size_t len) {
                firm::wire::dispatch_feed(m, len, [&](auto msg) { sink += msg.ts(); });
            });
    });
    ll::arb::Counts c;
    const double arb = per_item(clk, a.size() + b.size(), [&] { c = ll::arb::arbitrate(a, b); });
    do_not_optimize(sink);
    std::printf("decode,book1,%.2f\ndecode,flyweight,%.2f\ndecode,sbe,%.2f\ndecode,packets,%.2f\n", book1, flyweight, sbe,
                packets);
    const auto ca = ll::arb::line_counts(a), cb = ll::arb::line_counts(b);
    std::printf("messages,%zu,%zu\n", n, all);
    std::printf("line,A,%llu,%llu,%llu,%llu\nline,B,%llu,%llu,%llu,%llu\n", (unsigned long long)ca.packets,
                (unsigned long long)ca.messages, (unsigned long long)ca.gaps, (unsigned long long)ca.missing,
                (unsigned long long)cb.packets, (unsigned long long)cb.messages, (unsigned long long)cb.gaps,
                (unsigned long long)cb.missing);
    std::printf("arb,%llu,%llu,%llu,%llu,%llu,%.2f\n", (unsigned long long)c.packets, (unsigned long long)c.messages,
                (unsigned long long)c.gaps, (unsigned long long)c.missing, (unsigned long long)c.duplicates, arb);
    return 0;
}
