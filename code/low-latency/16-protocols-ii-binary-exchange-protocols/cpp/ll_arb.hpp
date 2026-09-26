// Chapter 16: line arbitration of two MoldUDP64 lines, and per-line gap counting.
#pragma once
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <vector>

#include "../../../firm/wirecodec/cpp/firm_wirecodec.hpp"

namespace ll::arb {

struct Packet {
    std::uint64_t t;          // arrival time at the recording point
    const std::uint8_t* p;    // the MoldUDP64 packet
    std::uint32_t n;
};

// Recorded file: send_ns u64 | length u32 | packet, big-endian.
inline std::vector<Packet> read_recorded(const std::vector<std::uint8_t>& f) {
    std::vector<Packet> out;
    for (std::size_t i = 0; i + 12 <= f.size();) {
        const auto n = static_cast<std::uint32_t>(firm::wire::be32(f.data() + i + 8));
        out.push_back({firm::wire::be64(f.data() + i), f.data() + i + 12, n});
        i += 12 + n;
    }
    return out;
}

struct Counts {
    std::uint64_t packets = 0, messages = 0, gaps = 0, missing = 0, duplicates = 0;
};

// Keeps each sequence number once, whichever line brings it first; a sequence number that neither line brought
// before a later one arrives is a gap: lost on both lines, to be recovered (retransmission or snapshot).
class Arbiter {
public:
    // Returns the number of new messages in the packet (0 for a duplicate or a heartbeat); `first` is the sequence
    // number of the first new one.
    std::uint64_t on_packet(const std::uint8_t* p, std::uint64_t& first) {
        const firm::wire::MoldHeader h{p};
        const std::uint64_t seq = h.seq();
        const std::uint64_t count = h.count() == 0xFFFF ? 0 : h.count();
        if (count != 0 && seq + count <= next_) {
            ++c.duplicates;
            return 0;
        }
        if (seq > next_) {
            ++c.gaps;
            c.missing += seq - next_;
        }
        first = seq > next_ ? seq : next_;
        const std::uint64_t fresh = seq + count - first;
        c.messages += fresh;
        ++c.packets;
        if (seq + count > next_) next_ = seq + count;
        return fresh;
    }
    std::uint64_t next() const { return next_; }
    Counts c;

private:
    std::uint64_t next_ = 1;
};

// Per-line gap counting (the same rule on one line alone).
inline Counts line_counts(const std::vector<Packet>& line) {
    Counts c;
    std::uint64_t next = 1;
    for (const auto& k : line) {
        const firm::wire::MoldHeader h{k.p};
        const std::uint64_t count = h.count() == 0xFFFF ? 0 : h.count();
        if (h.seq() > next) {
            ++c.gaps;
            c.missing += h.seq() - next;
        }
        c.messages += count;
        ++c.packets;
        if (h.seq() + count > next) next = h.seq() + count;
    }
    return c;
}

// Merge two lines in arrival order (line A first on a tie) through one arbiter.
inline Counts arbitrate(const std::vector<Packet>& a, const std::vector<Packet>& b) {
    Arbiter arb;
    std::size_t i = 0, j = 0;
    std::uint64_t first = 0;
    while (i < a.size() || j < b.size()) {
        const bool take_a = j == b.size() || (i < a.size() && a[i].t <= b[j].t);
        arb.on_packet(take_a ? a[i++].p : b[j++].p, first);
    }
    return arb.c;
}

}  // namespace ll::arb
