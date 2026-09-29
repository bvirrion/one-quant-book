// firm.netsim (C++20): the egress-queue kernel of One Quant Book 14, chapter 1 (Python reference: firm_netsim.py).
// A tail-drop FIFO at an output port: the backlog (wire bytes, frame in service included) drains at the line rate;
// an arriving frame that would overflow the buffer is dropped. Same arithmetic, same order of operations as the
// Python reference, so the two agree to the last bit on the shared fixture.
#pragma once
#include <algorithm>
#include <cstdint>
#include <vector>

namespace firm::netsim {

inline constexpr std::int64_t kOverhead = 20;   // preamble + start delimiter (8) + inter-frame gap (12)

struct EgressResult {
    std::vector<double> depart_ns;   // last bit on the wire; -1 if dropped
    std::vector<bool> dropped;
    double max_backlog = 0.0;
    std::int64_t n_dropped = 0, dropped_bytes = 0;
};

inline EgressResult egress(const std::vector<std::int64_t>& t_ns, const std::vector<std::int64_t>& frames,
                           double gbps, double buffer_bytes) {
    EgressResult r;
    const std::size_t n = t_ns.size();
    r.depart_ns.assign(n, -1.0);
    r.dropped.assign(n, false);
    const double rate = gbps / 8.0;
    double q = 0.0;
    std::int64_t prev = 0;
    for (std::size_t i = 0; i < n; ++i) {
        const std::int64_t w = frames[i] + kOverhead;
        q = std::max(0.0, q - static_cast<double>(t_ns[i] - prev) * rate);
        prev = t_ns[i];
        if (q + static_cast<double>(w) > buffer_bytes) {
            r.dropped[i] = true;
            ++r.n_dropped;
            r.dropped_bytes += w;
            continue;
        }
        q += static_cast<double>(w);
        r.max_backlog = std::max(r.max_backlog, q);
        r.depart_ns[i] = static_cast<double>(t_ns[i]) + q / rate;
    }
    return r;
}

}  // namespace firm::netsim
