// Chapter 21: what the order gateway costs.
//   ll_gateway_bench messages   ns per call (TSC around each, timer cost subtracted) for each step of an order's life:
//                               new order encoded, acknowledgement, partial fill, cancel encoded, cancel acknowledgement
//   ll_gateway_bench exposure   ns for one worst-case exposure check with n open orders: running sums (firm.ordergw),
//                               a scan of an array of orders, a scan of a hash map of orders
#include <cstdio>
#include <string>
#include <unordered_map>
#include <vector>

#include "firm_ordergw.hpp"
#include "firm_ubench.hpp"

using namespace firm::ogw;
namespace ub = firm::ubench;

static void messages(const ub::Clock& clk, double ovh) {
    constexpr int N = 200'000;
    Gateway g(Limits{1'000'000'000, 1'000'000'000});
    std::uint8_t out[64], ack[64], fill[64], cxl[64];
    std::vector<double> t[5];
    for (auto& v : t) v.reserve(N);
    const char* names[] = {"new order", "ack", "partial fill", "cancel", "cancel ack"};
    for (int i = 0; i < N + 1000; ++i) {
        const std::uint64_t cl = static_cast<std::uint64_t>(i) + 1;
        firm::wire::OutAWriter(ack).cl_ord_id(cl).qty(100).price(999'900).side('B');
        firm::wire::OutEWriter(fill).cl_ord_id(cl).qty(50).price(999'900).leaves(50);
        firm::wire::OutCWriter(cxl).cl_ord_id(cl).decrement(50).reason('U');
        std::uint64_t d[5];
        std::uint64_t a = ub::tsc_start();
        g.new_order(i, cl, 'B', 100, 999'900, out);
        d[0] = ub::rdtscp() - a;
        ub::do_not_optimize(out[0]);
        a = ub::tsc_start();
        g.on_wire(ack, firm::wire::OutA::kLength);
        d[1] = ub::rdtscp() - a;
        a = ub::tsc_start();
        g.on_wire(fill, firm::wire::OutE::kLength);
        d[2] = ub::rdtscp() - a;
        a = ub::tsc_start();
        g.cancel(i, cl, out);
        d[3] = ub::rdtscp() - a;
        ub::do_not_optimize(out[0]);
        a = ub::tsc_start();
        g.on_wire(cxl, firm::wire::OutC::kLength);
        d[4] = ub::rdtscp() - a;
        if (i >= 1000)
            for (int k = 0; k < 5; ++k) t[k].push_back(clk.ns(d[k]) - ovh);
    }
    if (g.position() != 50LL * (N + 1000) || g.open_orders() != 0) std::printf("error,state\n");
    for (int k = 0; k < 5; ++k)
        for (const double q : {0.5, 0.99})
            std::printf("messages,%s,%g,%.1f\n", names[k], q, ub::quantile(t[k], q));
}

static void exposure(const ub::Clock& clk, double ovh) {
    for (const int n : {1, 10, 100, 1000, 10000}) {
        Gateway g(Limits{1'000'000'000, 1'000'000'000});
        std::vector<Order> arr;
        std::unordered_map<std::uint64_t, Order> map;
        std::uint8_t out[64];
        for (int i = 0; i < n; ++i) {
            const std::uint64_t cl = static_cast<std::uint64_t>(i) + 1;
            g.new_order(0, cl, i % 2 ? 'S' : 'B', 100, 999'900, out);
            arr.push_back(*g.find(cl));
            map.emplace(cl, arr.back());
        }
        auto scan_arr = [&] {
            std::int64_t w = 0;
            for (const Order& o : arr) w += o.side == 'B' ? o.worst_leaves() : 0;
            ub::do_not_optimize(w);
        };
        auto scan_map = [&] {
            std::int64_t w = 0;
            for (const auto& [cl, o] : map) w += o.side == 'B' ? o.worst_leaves() : 0;
            ub::do_not_optimize(w);
        };
        auto sums = [&] { ub::do_not_optimize(g.worst_long()); };
        const std::size_t reps = n >= 1000 ? 2000 : 20000;
        auto q = [&](auto&& f) {
            std::vector<double> v;
            for (auto x : ub::run(f, reps, 200)) v.push_back(clk.ns(x) - ovh);
            return ub::quantile(v, 0.5);
        };
        std::printf("exposure,%d,%.1f,%.1f,%.1f\n", n, q(sums), q(scan_arr), q(scan_map));
    }
}

int main(int argc, char** argv) {
    const std::string mode = argc > 1 ? argv[1] : "messages";
    const ub::Clock clk = ub::Clock::calibrate();
    const double ovh = clk.ns(ub::overhead());
    if (mode == "messages") messages(clk, ovh);
    else exposure(clk, ovh);
    return 0;
}
