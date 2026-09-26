// Chapter 16: the arbiter on scripted lines -- A loses packets 3 and 6, B loses 3 and 5: the arbitrated stream has
// one gap (packet 3, lost on both) and every other message once.
#include "ll_arb.hpp"
#include "../../../firm/wirecodec/cpp/firm_wirecodec.hpp"

#include <cstdio>

using namespace ll::arb;

static std::vector<std::uint8_t> packet(std::uint64_t seq, std::uint16_t count) {
    std::vector<std::uint8_t> p(20, ' ');
    firm::wire::put_be(p.data() + 10, seq, 8);
    firm::wire::put_be(p.data() + 18, count, 2);
    for (std::uint16_t k = 0; k < count; ++k) {   // messages of one byte: a system event stub
        p.push_back(0);
        p.push_back(1);
        p.push_back('S');
    }
    return p;
}

int main() {
    // eight packets of two messages each: sequence numbers 1, 3, 5, ..., 15
    std::vector<std::vector<std::uint8_t>> store;
    for (int k = 0; k < 8; ++k) store.push_back(packet(1 + 2 * static_cast<std::uint64_t>(k), 2));
    std::vector<Packet> a, b;
    for (int k = 0; k < 8; ++k) {
        const auto* p = store[static_cast<std::size_t>(k)].data();
        const auto n = static_cast<std::uint32_t>(store[static_cast<std::size_t>(k)].size());
        if (k != 2 && k != 5) a.push_back({100ULL * static_cast<std::uint64_t>(k), p, n});
        if (k != 2 && k != 4) b.push_back({100ULL * static_cast<std::uint64_t>(k) + 7, p, n});
    }
    const Counts ca = line_counts(a), cb = line_counts(b), c = arbitrate(a, b);
    std::printf("A: %llu gaps, B: %llu gaps, arbitrated: %llu gap(s), %llu missing, %llu duplicates\n",
                static_cast<unsigned long long>(ca.gaps), static_cast<unsigned long long>(cb.gaps),
                static_cast<unsigned long long>(c.gaps), static_cast<unsigned long long>(c.missing),
                static_cast<unsigned long long>(c.duplicates));
    if (ca.gaps != 2 || ca.missing != 4 || cb.gaps != 2 || cb.missing != 4) return 1;
    if (c.gaps != 1 || c.missing != 2 || c.messages != 14 || c.duplicates != 5) return 2;
    return 0;
}
