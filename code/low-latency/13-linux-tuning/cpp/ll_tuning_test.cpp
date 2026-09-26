// Chapter 13: the hiccup meter on a scripted clock, and page faults with and without mlockall.
#include "ll_tuning.hpp"

#include <sys/mman.h>

#include <cstdio>

using namespace ll::tuning;

int main() {
    // A clock that advances 10 ticks per reading, except for three stalls of 500, 2000 and 90 ticks.
    std::uint64_t t = 0, calls = 0;
    auto fake = [&] {
        ++calls;
        t += calls == 50 ? 500 : calls == 120 ? 2000 : calls == 200 ? 90 : 10;
        return t;
    };
    const Hiccups h = hiccup_meter(fake, 5000, 50, 16);
    if (h.gaps.size() != 3 || h.worst != 2000 || h.stolen != 2590 || h.elapsed < 5000) return 1;
    const auto ex = exceedance(h.gaps, {50, 100, 1000, 5000});
    if (ex != std::vector<std::uint64_t>{3, 2, 1, 0}) return 2;

    // Without locking, the first write to each page of a fresh mapping faults.
    constexpr std::size_t kBytes = 8u << 20;
    void* a = mmap(nullptr, kBytes, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    const long cold = touch_faults(static_cast<char*>(a), kBytes);
    munmap(a, kBytes);
    if (cold < 2000) return 3;   // 2,048 pages (fewer only if the kernel used huge pages)

    // With MCL_FUTURE the kernel populates new mappings when they are made: the writes then take no fault.
    const int err = lock_all();
    if (err != 0) {
        std::printf("mlockall failed (errno %d): lock test skipped; cold faults %ld\n", err, cold);
        return 0;
    }
    void* b = mmap(nullptr, kBytes, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    const long locked = touch_faults(static_cast<char*>(b), kBytes);
    munmap(b, kBytes);
    munlockall();
    std::printf("faults on 8 MiB: %ld unlocked, %ld after mlockall\n", cold, locked);
    return locked < 16 ? 0 : 4;
}
