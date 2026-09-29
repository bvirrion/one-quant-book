// Writes one line per datagram: mode,sent_ns,kernel_ns,app_ns (driven by ../python/bench_rx.py).
#include <cstdio>
#include <cstdlib>

#include "nw_rx.hpp"

int main(int argc, char** argv) {
    const int n = argc > 1 ? std::atoi(argv[1]) : 20000;
    const long gap = argc > 2 ? std::atol(argv[2]) : 20000;
    std::puts("mode,sent_ns,kernel_ns,app_ns");
    for (int mode = 0; mode < 3; ++mode) {
        nw_rx::run(mode, 2000, gap);                   // warm-up
        for (const auto& x : nw_rx::run(mode, n, gap))
            std::printf("%d,%lld,%lld,%lld\n", mode, static_cast<long long>(x.sent), static_cast<long long>(x.kernel),
                        static_cast<long long>(x.app));
    }
    return 0;
}
