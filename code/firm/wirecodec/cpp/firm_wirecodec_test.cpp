// firm.wirecodec (generated C++20 flyweights): every message of Book 10's golden fixtures decodes to the golden CSV
// values, re-encodes to the same bytes, and survives the round trip through the little-endian SBE-style layout.
#include "firm_wirecodec_bridge.hpp"

#include <cstdio>
#include <fstream>
#include <iterator>
#include <sstream>
#include <string>
#include <vector>

using namespace firm::wire;

static int fails = 0;

static std::vector<std::uint8_t> bytes(const std::string& path) {
    std::ifstream f(path, std::ios::binary);
    return {std::istreambuf_iterator<char>(f), {}};
}

template <class Dispatch>
static std::size_t check(const char* proto, char type, Dispatch dispatch) {
    const std::string dir = "code/firm/exchsim/data/golden/";
    const auto bin = bytes(dir + proto + ".bin");
    std::ifstream rows(dir + proto + "_" + type + ".csv");
    std::string line;
    std::getline(rows, line);   // header
    std::size_t n = 0;
    while (std::getline(rows, line)) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        const std::size_t comma = line.find(',');
        const std::size_t off = std::stoul(line.substr(0, comma));
        const std::string want = line.substr(comma + 1);
        const std::size_t len = be16(bin.data() + off);
        const std::uint8_t* p = bin.data() + off + 2;
        std::string got;
        std::vector<std::uint8_t> again(len);
        const bool ok = dispatch(p, len, [&](auto m) {
            got = csv(m);
            rewrite(m, again.data());
        });
        if (!ok || got != want || !std::equal(again.begin(), again.end(), p)) {
            if (fails++ < 5) std::printf("%s %c at %zu:\n  got  %s\n  want %s\n", proto, type, off, got.c_str(), want.c_str());
        }
        ++n;
    }
    return n;
}

int main() {
    // Every type letter: a type with no golden CSV (no such message in the fixture day) contributes nothing, so new
    // message types in the schema are covered as soon as Book 10's fixtures contain them.
    const std::string letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
    std::size_t total = 0;
    for (const char t : letters) {
        total += check("feed", t, [](auto p, auto n, auto v) { return dispatch_feed(p, n, v); });
        total += check("in", t, [](auto p, auto n, auto v) { return dispatch_in(p, n, v); });
        total += check("out", t, [](auto p, auto n, auto v) { return dispatch_out(p, n, v); });
        total += check("ctl", t, [](auto p, auto n, auto v) { return dispatch_ctl(p, n, v); });
    }
    if (total < 4000) ++fails;

    // Every feed message through the SBE-style layout and back to the same values.
    const auto feed = bytes("code/firm/exchsim/data/golden/feed.bin");
    std::size_t sbe = 0;
    for (std::size_t i = 0; i + 2 <= feed.size();) {
        const std::size_t len = be16(feed.data() + i);
        const std::uint8_t* p = feed.data() + i + 2;
        std::uint8_t out[128];
        const std::size_t k = to_sbe(p, len, out);
        const firm::sbe::Header h{out};
        std::string a, b;
        dispatch_feed(p, len, [&](auto m) { a = csv(m); });
        auto dec = [&](auto msg) { b = csv(msg); };
        switch (h.template_id()) {
#define SBE_CASE(T) case firm::sbe::Feed##T::kTemplateId: dec(firm::sbe::Feed##T{out + firm::sbe::kHeader}); break;
            SBE_CASE(A) SBE_CASE(E) SBE_CASE(X) SBE_CASE(D) SBE_CASE(P) SBE_CASE(U) SBE_CASE(C) SBE_CASE(Q)
            SBE_CASE(I) SBE_CASE(S) SBE_CASE(H) SBE_CASE(R) SBE_CASE(G) SBE_CASE(W)
#undef SBE_CASE
            default: break;
        }
        if (k == 0 || a != b || h.schema_id() != firm::sbe::kSchemaId) {
            if (fails++ < 5) std::printf("sbe round trip at %zu: %s vs %s\n", i, a.c_str(), b.c_str());
        }
        ++sbe;
        i += 2 + len;
    }
    std::printf("%s: %zu golden messages decoded and re-encoded, %zu through the SBE layout\n",
                fails ? "FAILED" : "ok", total, sbe);
    return fails ? 1 : 0;
}
