// Chapter 18 benchmark.
//   handle <lineA> <lineB> <clean> <snapshot>   the feed handler on recorded lines, retransmission server on: time to
//                                               handle each input (TSC), as quantiles; prints "handle,<q>,<ns>" lines
//   rcvbuf <packets> <bytes>                    a UDP burst on loopback while the receiver is stalled, for several
//                                               SO_RCVBUF sizes: "rcvbuf,<payload>,<asked>,<granted>,<received>"
#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>

#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iterator>
#include <string>
#include <vector>

#include "firm_feedhandler.hpp"
#include "firm_ubench.hpp"

using namespace firm::ubench;

static std::vector<std::uint8_t> file(const char* path) {
    std::ifstream f(path, std::ios::binary);
    return {std::istreambuf_iterator<char>(f), {}};
}

static std::uint64_t tsc() { return rdtscp(); }

static void handle(char** argv, const Clock& clk) {
    const auto fa = file(argv[2]), fb = file(argv[3]), fc = file(argv[4]), fs = file(argv[5]);
    const auto a = firm::feed2::recorded(fa), b = firm::feed2::recorded(fb), c = firm::feed2::recorded(fc),
               s = firm::feed2::recorded(fs);
    const firm::feed2::RetxServer server(c, 100'000);
    std::vector<std::uint32_t> t;
    t.reserve(a.size() + b.size() + s.size() + 1000);
    for (int warm = 0; warm < 2; ++warm) {   // the second pass is the measured one, caches and branch history warm
        t.clear();
        firm::feed2::Handler h(&server);
        h.clock = tsc;
        h.timings = &t;
        h.run(a, b, s);
        if (warm == 1)
            std::printf("events,%llu,%016llx\n", static_cast<unsigned long long>(h.events),
                        static_cast<unsigned long long>(h.hash));
    }
    std::vector<double> ns(t.size());
    for (std::size_t i = 0; i < t.size(); ++i) ns[i] = clk.ns(t[i]);
    for (const double q : {0.5, 0.9, 0.99, 0.999, 1.0}) std::printf("handle,%g,%.0f\n", q, quantile(ns, q));
    std::printf("inputs,%zu\n", ns.size());
}

// A handler that stalls (a recovery, a descheduled thread) during a burst: the burst is sent while nobody reads, then
// the socket is drained. What survives is what the receive buffer held: its capacity in datagrams.
static void rcvbuf(int packets, int size) {
    for (const int asked : {16384, 65536, 262144, 1048576, 2097152, 4194304}) {
        const int rx = socket(AF_INET, SOCK_DGRAM, 0), tx = socket(AF_INET, SOCK_DGRAM, 0);
        setsockopt(rx, SOL_SOCKET, SO_RCVBUF, &asked, sizeof asked);
        int granted = 0;
        socklen_t gl = sizeof granted;
        getsockopt(rx, SOL_SOCKET, SO_RCVBUF, &granted, &gl);
        sockaddr_in addr{};
        addr.sin_family = AF_INET;
        addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
        bind(rx, reinterpret_cast<sockaddr*>(&addr), sizeof addr);
        socklen_t al = sizeof addr;
        getsockname(rx, reinterpret_cast<sockaddr*>(&addr), &al);
        std::vector<char> msg(static_cast<std::size_t>(size), 'x');
        for (int i = 0; i < packets; ++i)
            sendto(tx, msg.data(), msg.size(), 0, reinterpret_cast<sockaddr*>(&addr), sizeof addr);
        int received = 0;
        char buf[2048];
        while (recv(rx, buf, sizeof buf, MSG_DONTWAIT) > 0) ++received;
        std::printf("rcvbuf,%d,%d,%d,%d\n", size, asked, granted, received);
        close(rx);
        close(tx);
    }
}

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    const std::string mode = argv[1];
    const Clock clk = Clock::calibrate();
    if (mode == "handle" && argc >= 6) handle(argv, clk);
    else if (mode == "rcvbuf" && argc >= 4) rcvbuf(std::atoi(argv[2]), std::atoi(argv[3]));
    else return 1;
    return 0;
}
