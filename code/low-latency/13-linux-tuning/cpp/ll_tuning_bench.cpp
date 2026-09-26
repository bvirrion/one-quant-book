// Chapter 13 benchmark: what an untuned machine does to a thread that wants to run without interruption.
//   hiccup <seconds> <compete 0|1>   spin on the time-stamp counter, record every gap (optionally beside a competing
//                                    spinner on the same CPUs); prints "summary,..." and "exc,<ns>,<count>" lines
//   ctx <round trips> <cpu> <cpu>    ping-pong over two pipes between two threads (two context switches per trip
//                                    when both threads share one CPU)
//   udp <round trips> <block|spin> <cpu client> <cpu echo>   loopback UDP echo, blocking or busy-polling receive
//   mlock <MiB>                      page faults and time to touch fresh memory, without and with mlockall
//   privileges                       what an unprivileged process may ask for: SCHED_FIFO, SO_BUSY_POLL
#include <arpa/inet.h>
#include <fcntl.h>
#include <netinet/in.h>
#include <pthread.h>
#include <sched.h>
#include <sys/socket.h>
#include <unistd.h>

#include <algorithm>
#include <atomic>
#include <cerrno>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <thread>
#include <vector>

#include "firm_ubench.hpp"
#include "ll_tuning.hpp"

using namespace firm::ubench;
using namespace ll::tuning;

static void pin(int cpu) {
    cpu_set_t s;
    CPU_ZERO(&s);
    CPU_SET(cpu, &s);
    pthread_setaffinity_np(pthread_self(), sizeof s, &s);
}

static void quantiles(const char* name, std::vector<double>& t) {
    std::printf("%s,%.0f,%.0f,%.0f,%.0f\n", name, quantile(t, 0.5), quantile(t, 0.99), quantile(t, 0.999),
                quantile(t, 1.0));
}

static void hiccup(double seconds, bool compete, const Clock& clk) {
    std::atomic<bool> stop{false};
    std::thread rival;
    if (compete)
        rival = std::thread([&] {
            while (!stop.load(std::memory_order_relaxed)) clobber();
        });
    const auto dur = static_cast<std::uint64_t>(seconds * 1e9 * clk.ticks_per_ns);
    const auto thr = static_cast<std::uint64_t>(200 * clk.ticks_per_ns);   // 200 ns: far above one loop
    const Hiccups h = hiccup_meter([] { return rdtscp(); }, dur, thr, 1u << 22);
    stop = true;
    if (rival.joinable()) rival.join();
    std::printf("summary,%.0f,%zu,%.0f,%.0f,%llu\n", clk.ns(h.elapsed), h.gaps.size(), clk.ns(h.stolen),
                clk.ns(h.worst), static_cast<unsigned long long>(h.loops));
    const double grid[] = {200, 500, 1e3, 2e3, 5e3, 1e4, 2e4, 5e4, 1e5, 2e5, 5e5, 1e6, 2e6, 5e6, 1e7, 2e7, 5e7};
    std::vector<std::uint64_t> thr_ticks;
    for (const double g : grid) thr_ticks.push_back(static_cast<std::uint64_t>(g * clk.ticks_per_ns));
    const auto ex = exceedance(h.gaps, thr_ticks);
    for (std::size_t i = 0; i < ex.size(); ++i)
        std::printf("exc,%.0f,%llu\n", grid[i], static_cast<unsigned long long>(ex[i]));
    // A message arriving at a random moment waits for the rest of the gap it falls in: it waits longer than x with
    // probability sum(max(g - x, 0)) / T, and on average sum(g^2) / (2T).
    double sq = 0;
    for (const auto g : h.gaps) sq += clk.ns(g) * clk.ns(g);
    std::printf("meanwait,%.3f\n", sq / (2 * clk.ns(h.elapsed)));
    for (const double x : grid) {
        double s = 0;
        for (const auto g : h.gaps) s += std::max(0.0, clk.ns(g) - x);
        std::printf("wait,%.0f,%.3e\n", x, s / clk.ns(h.elapsed));
    }
}

static void ctx(int trips, int cpu_a, int cpu_b, const Clock& clk) {
    int ab[2], ba[2];
    if (pipe(ab) != 0 || pipe(ba) != 0) std::exit(1);
    std::thread echo([&] {
        pin(cpu_b);
        char c;
        for (int i = 0; i < trips + 100; ++i)
            if (read(ab[0], &c, 1) != 1 || write(ba[1], &c, 1) != 1) std::exit(1);
    });
    pin(cpu_a);
    std::vector<double> t;
    t.reserve(static_cast<std::size_t>(trips));
    char c = 'x';
    for (int i = 0; i < trips + 100; ++i) {
        const std::uint64_t a = tsc_start();
        if (write(ab[1], &c, 1) != 1 || read(ba[0], &c, 1) != 1) std::exit(1);
        if (i >= 100) t.push_back(clk.ns(rdtscp() - a));
    }
    echo.join();
    quantiles(cpu_a == cpu_b ? "pipe-same" : "pipe-two", t);
}

static int udp_socket(int port) {
    const int s = socket(AF_INET, SOCK_DGRAM, 0);
    sockaddr_in a{};
    a.sin_family = AF_INET;
    a.sin_port = htons(static_cast<std::uint16_t>(port));
    a.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    if (bind(s, reinterpret_cast<sockaddr*>(&a), sizeof a) != 0) std::exit(2);
    return s;
}

// Receive one datagram: a blocking call that sleeps until data arrives, or a loop of non-blocking calls that never
// gives up the CPU (busy polling from user space).
static ssize_t receive(int s, char* buf, bool spin) {
    if (!spin) return recv(s, buf, 64, 0);
    for (;;) {
        const ssize_t n = recv(s, buf, 64, MSG_DONTWAIT);
        if (n >= 0 || errno != EAGAIN) return n;
    }
}

static void udp(int trips, bool spin, int cpu_a, int cpu_b, const Clock& clk) {
    const int port_a = 40000 + (getpid() % 10000), port_b = port_a + 1;
    const int sa = udp_socket(port_a), sb = udp_socket(port_b);
    sockaddr_in to_a{}, to_b{};
    to_a.sin_family = to_b.sin_family = AF_INET;
    to_a.sin_addr.s_addr = to_b.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    to_a.sin_port = htons(static_cast<std::uint16_t>(port_a));
    to_b.sin_port = htons(static_cast<std::uint16_t>(port_b));
    std::thread echo([&] {
        pin(cpu_b);
        char buf[64];
        for (int i = 0; i < trips + 100; ++i) {
            const ssize_t n = receive(sb, buf, spin);
            if (n != 64) std::exit(3);
            sendto(sb, buf, 64, 0, reinterpret_cast<sockaddr*>(&to_a), sizeof to_a);
        }
    });
    pin(cpu_a);
    char msg[64] = {};
    std::vector<double> t;
    t.reserve(static_cast<std::size_t>(trips));
    for (int i = 0; i < trips + 100; ++i) {
        const std::uint64_t a = tsc_start();
        sendto(sa, msg, 64, 0, reinterpret_cast<sockaddr*>(&to_b), sizeof to_b);
        if (receive(sa, msg, spin) != 64) std::exit(4);
        if (i >= 100) t.push_back(clk.ns(rdtscp() - a));
    }
    echo.join();
    close(sa);
    close(sb);
    quantiles(spin ? "udp-spin" : "udp-block", t);
}

static void mlock_faults(std::size_t mib) {
    const std::size_t bytes = mib << 20;
    const double p = static_cast<double>(bytes / 4096);
    void* a = mmap(nullptr, bytes, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    double w0 = raw_ns();
    const long cold = touch_faults(static_cast<char*>(a), bytes);
    const double cold_ns = (raw_ns() - w0) / p;
    munmap(a, bytes);
    const int err = lock_all();
    w0 = raw_ns();
    void* b = mmap(nullptr, bytes, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    const double map_ns = (raw_ns() - w0) / p;
    w0 = raw_ns();
    const long locked = touch_faults(static_cast<char*>(b), bytes);
    const double warm_ns = (raw_ns() - w0) / p;
    std::printf("unlocked,%ld,0,%.1f\nlocked,%ld,%.1f,%.1f\nerrno,%d\n", cold, cold_ns, locked, map_ns, warm_ns, err);
}

static void privileges() {
    sched_param sp{};
    sp.sched_priority = 1;
    const int fifo = sched_setscheduler(0, SCHED_FIFO, &sp) == 0 ? 0 : errno;
    const int s = socket(AF_INET, SOCK_DGRAM, 0);
    int us = 50;
    const int bp = setsockopt(s, SOL_SOCKET, SO_BUSY_POLL, &us, sizeof us) == 0 ? 0 : errno;
    std::printf("SCHED_FIFO,%s\nSO_BUSY_POLL,%s\n", fifo ? strerrorname_np(fifo) : "ok", bp ? strerrorname_np(bp) : "ok");
}

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    const std::string mode = argv[1];
    const Clock clk = Clock::calibrate();
    if (mode == "hiccup") hiccup(std::atof(argv[2]), std::atoi(argv[3]) != 0, clk);
    else if (mode == "ctx") ctx(std::atoi(argv[2]), std::atoi(argv[3]), std::atoi(argv[4]), clk);
    else if (mode == "udp") udp(std::atoi(argv[2]), std::string(argv[3]) == "spin", std::atoi(argv[4]), std::atoi(argv[5]), clk);
    else if (mode == "mlock") mlock_faults(static_cast<std::size_t>(std::atoi(argv[2])));
    else if (mode == "privileges") privileges();
    else return 1;
    return 0;
}
