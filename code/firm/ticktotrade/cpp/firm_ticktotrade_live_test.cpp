// firm.ticktotrade (C++20): one live run of the harness on the loopback interface, a few hundred milliseconds with four
// threads: the orders sent equal the offline replay's (data/expected.txt), every order carries stamps in path order
// from the exchange's send to the venue's receipt, and nothing is allocated after warm-up.
#include "firm_ticktotrade_live.hpp"

#include <cstdio>
#include <fstream>
#include <iterator>

using namespace firm::t2t;

int main() {
    std::ifstream f("code/firm/ticktotrade/data/line.bin", std::ios::binary);
    Config cfg;
    cfg.line.assign(std::istreambuf_iterator<char>(f), {});
    cfg.stretch = 40.0;
    const Result r = run_live(cfg);
    std::ifstream ef("code/firm/ticktotrade/data/expected.txt");
    const std::string want{std::istreambuf_iterator<char>(ef), {}};
    char h[17];
    std::snprintf(h, sizeof h, "%016llx", static_cast<unsigned long long>(order_hash(r.out)));
    std::size_t ordered = 0, received = 0;
    for (const auto& o : r.orders) {
        bool ok = o.exch && o.exch <= o.s.t[Recv];
        for (int i = Recv; i + 1 < NStamps; ++i) ok = ok && o.s.t[i] <= o.s.t[i + 1];
        ordered += ok;
        received += o.venue != 0 && o.venue >= o.s.t[Encode];  // on loopback, send() delivers before it returns
    }
    std::printf("events %llu, packets %llu + %llu (duplicates %llu), orders %zu, hash %s\n",
                static_cast<unsigned long long>(r.events), static_cast<unsigned long long>(r.packets_a),
                static_cast<unsigned long long>(r.packets_b), static_cast<unsigned long long>(r.duplicates),
                r.orders.size(), h);
    std::printf("stamps in order %zu, received by the venue %zu, allocations after warm-up %lld\n", ordered, received,
                r.allocations_after_warmup);
    const bool ok = want.find(h) != std::string::npos && r.events == 6000 && ordered == r.orders.size() &&
                    received == r.orders.size() && r.allocations_after_warmup == 0;
    std::printf(ok ? "ok\n" : "FAIL\n");
    return ok ? 0 : 1;
}
