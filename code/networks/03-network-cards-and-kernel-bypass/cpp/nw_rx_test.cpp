// A small run of each receive mode on loopback: every datagram arrives, and for each one the kernel's timestamp lies
// between its send time and the application's read time. Machine-independent: no latency is asserted.
#include <cstdio>

#include "nw_rx.hpp"

int main() {
    int bad = 0;
    for (int mode = 0; mode < 3; ++mode) {
        const auto s = nw_rx::run(mode, 320, 20'000);
        int order = 0;
        for (const auto& x : s)
            if (!(x.sent <= x.kernel && x.kernel <= x.app)) ++order;
        std::printf("mode %d: %zu datagrams, %d out of order\n", mode, s.size(), order);
        if (s.size() != 320 || order > 0) ++bad;
    }
    return bad;
}
