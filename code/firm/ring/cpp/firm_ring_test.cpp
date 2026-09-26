// Acceptance test of firm.ring, C++ side: the shared byte layout (fixture), SPSC order under two threads, broadcast
// overrun detection, seqlock consistency, and a ring shared with a child process over shared memory.
#include "firm_ring.hpp"

#include <sys/wait.h>

#include <cstdio>
#include <fstream>
#include <iterator>
#include <thread>
#include <vector>

using namespace firm::ring;

static int fail(const char* what) { std::printf("FAIL %s\n", what); return 1; }

int main() {
    std::ifstream f("code/firm/ring/data/ring_image.bin", std::ios::binary);
    const std::vector<std::uint8_t> fixture{std::istreambuf_iterator<char>(f), std::istreambuf_iterator<char>()};
    std::vector<std::uint8_t> mem(region_size(8, 64));
    format(mem.data(), 8, 64);
    Spsc s(mem.data());
    char buf[64];
    for (int k = 0; k < 5; ++k) { const std::string m = "msg-" + std::to_string(k); if (!s.try_write(m.data(), static_cast<std::uint32_t>(m.size()))) return fail("write"); }
    for (int k = 0; k < 2; ++k) if (s.try_read(buf, sizeof buf) != 5) return fail("read");
    if (mem != fixture) return fail("layout differs from the fixture");
    std::vector<std::uint8_t> copy = fixture;
    Spsc t(copy.data());
    for (int k = 2; k < 5; ++k) { const int n = t.try_read(buf, sizeof buf); if (n != 5 || std::string(buf, 5) != "msg-" + std::to_string(k)) return fail("fixture read"); }
    if (t.try_read(buf, sizeof buf) != -1) return fail("empty");

    // SPSC under two threads: 200,000 messages in order
    std::vector<std::uint8_t> big(region_size(1024, 64));
    format(big.data(), 1024, 64);
    Spsc p(big.data()), c(big.data());
    std::thread prod([&] { for (std::uint64_t i = 0; i < 200'000; ++i) while (!p.try_write(&i, 8)) {} });
    for (std::uint64_t i = 0; i < 200'000; ++i) {
        std::uint64_t v;
        while (c.try_read(&v, 8) < 0) {}
        if (v != i) { prod.join(); return fail("order"); }
    }
    prod.join();

    // Broadcast: a reader lapped by the producer sees Overrun, then resynchronises
    std::vector<std::uint8_t> bm(region_size(8, 64));
    format(bm.data(), 8, 64);
    Broadcast b(bm.data());
    std::uint64_t pos = 0;
    std::uint32_t len = 0;
    if (b.read(pos, buf, len) != Broadcast::Read::Empty) return fail("broadcast empty");
    for (std::uint32_t i = 0; i < 20; ++i) b.write(&i, 4);
    if (b.read(pos, buf, len) != Broadcast::Read::Overrun) return fail("overrun not detected");
    pos = b.head() - 8;
    std::uint32_t got;
    if (b.read(pos, &got, len) != Broadcast::Read::Ok || got != 12) return fail("resync");

    // SeqLock: the reader never sees a half-written pair
    struct Top { std::int64_t bid, ask; };
    SeqLock<Top> top;
    top.store(Top{-1, 0});  // a consistent initial value
    std::atomic<bool> stop{false};
    std::thread w([&] { for (std::int64_t i = 0; !stop.load(); ++i) top.store(Top{i, i + 1}); });
    std::uint64_t retries = 0;
    for (int i = 0; i < 200'000; ++i) { const Top v = top.load(&retries); if (v.ask != v.bid + 1) { stop = true; w.join(); return fail("torn read"); } }
    stop = true;
    w.join();

    // Shared memory: a child process writes 1,000 messages, the parent reads them
    const std::string name = "/firm_ring_test_" + std::to_string(getpid());
    Segment seg(name, region_size(64, 64), true);
    format(seg.data(), 64, 64);
    const pid_t child = fork();
    if (child == 0) {
        Segment view(name, region_size(64, 64), false);
        Spsc cp(view.data());
        for (std::uint64_t i = 0; i < 1000; ++i) while (!cp.try_write(&i, 8)) {}
        _exit(0);
    }
    Spsc cr(seg.data());
    for (std::uint64_t i = 0; i < 1000; ++i) { std::uint64_t v; while (cr.try_read(&v, 8) < 0) {} if (v != i) return fail("shm order"); }
    int status = 0;
    waitpid(child, &status, 0);
    std::printf("ring ok (%llu seqlock retries)\n", static_cast<unsigned long long>(retries));
    return 0;
}
