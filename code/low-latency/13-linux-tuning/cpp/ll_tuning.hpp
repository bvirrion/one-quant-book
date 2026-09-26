// Chapter 13: the pieces of the tuning measurements that can be tested -- the hiccup meter's loop (any clock),
// the exceedance counts drawn from its gaps, and page-fault counting around memory locking.
#pragma once
#include <sys/mman.h>
#include <sys/resource.h>

#include <cerrno>
#include <cstddef>
#include <cstdint>
#include <vector>

namespace ll::tuning {

struct Hiccups {
    std::uint64_t loops = 0;      // clock readings taken
    std::uint64_t elapsed = 0;    // ticks from first to last reading
    std::uint64_t stolen = 0;     // ticks inside gaps above the threshold: time the thread did not run
    std::uint64_t worst = 0;      // longest gap, ticks
    std::vector<std::uint64_t> gaps;   // every gap above the threshold, ticks
};

// Spin reading `now()` for `duration` ticks; every gap between consecutive readings longer than `threshold` is a
// moment when this thread was not running (an interrupt, the tick, another task). Gaps go into a buffer reserved
// before the loop, so the loop itself never allocates.
template <class Now>
Hiccups hiccup_meter(Now now, std::uint64_t duration, std::uint64_t threshold, std::size_t max_gaps) {
    Hiccups h;
    h.gaps.reserve(max_gaps);
    const std::uint64_t start = now();
    std::uint64_t prev = start;
    while (prev - start < duration) {
        const std::uint64_t t = now();
        const std::uint64_t gap = t - prev;
        if (gap > threshold) {
            h.stolen += gap;
            if (gap > h.worst) h.worst = gap;
            if (h.gaps.size() < max_gaps) h.gaps.push_back(gap);
        }
        prev = t;
        ++h.loops;
    }
    h.elapsed = prev - start;
    return h;
}

// Number of gaps of at least each threshold (the exceedance curve of the chapter's figure).
inline std::vector<std::uint64_t> exceedance(const std::vector<std::uint64_t>& gaps,
                                             const std::vector<std::uint64_t>& thresholds) {
    std::vector<std::uint64_t> out(thresholds.size(), 0);
    for (const auto g : gaps)
        for (std::size_t i = 0; i < thresholds.size(); ++i)
            if (g >= thresholds[i]) ++out[i];
    return out;
}

inline long minor_faults() {
    rusage u{};
    getrusage(RUSAGE_SELF, &u);
    return u.ru_minflt;
}

// Write one byte per 4 KiB page; returns the minor page faults the writes took.
inline long touch_faults(volatile char* p, std::size_t bytes) {
    const long f0 = minor_faults();
    for (std::size_t i = 0; i < bytes; i += 4096) p[i] = 1;
    return minor_faults() - f0;
}

// Lock every present and future page of the process in memory: 0, or the errno (ENOMEM above RLIMIT_MEMLOCK,
// EPERM without the privilege).
inline int lock_all() { return mlockall(MCL_CURRENT | MCL_FUTURE) == 0 ? 0 : errno; }

}  // namespace ll::tuning
