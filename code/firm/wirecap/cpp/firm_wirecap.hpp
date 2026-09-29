// firm.wirecap (C++20): a reader of nanosecond libpcap files (One Quant Book 14, chapter 5), allocation-free per
// record: it walks the file in memory and hands each record's timestamp and bytes to a callback.
#pragma once
#include <cstdint>
#include <cstring>
#include <span>
#include <vector>

namespace firm::wirecap {

inline constexpr std::uint32_t kMagicNs = 0xA1B23C4Du;

struct Record { std::uint64_t t_ns; std::span<const std::uint8_t> frame; };

// Returns the number of records, or -1 if the header is not a nanosecond Ethernet pcap.
template <class F>
long for_each_record(const std::vector<std::uint8_t>& file, F&& f) {
    auto u32 = [&](std::size_t off) { std::uint32_t v; std::memcpy(&v, file.data() + off, 4); return v; };
    if (file.size() < 24 || u32(0) != kMagicNs || u32(20) != 1) return -1;
    long n = 0;
    std::size_t off = 24;
    while (off + 16 <= file.size()) {
        const std::uint64_t t = std::uint64_t(u32(off)) * 1'000'000'000ULL + u32(off + 4);
        const std::uint32_t incl = u32(off + 8);
        if (off + 16 + incl > file.size()) break;
        f(Record{t, std::span<const std::uint8_t>(file.data() + off + 16, incl)});
        off += 16 + incl;
        ++n;
    }
    return n;
}

}  // namespace firm::wirecap
