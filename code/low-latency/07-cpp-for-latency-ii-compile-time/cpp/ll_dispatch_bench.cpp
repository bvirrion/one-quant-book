// Chapter 7 benchmark: ns per message for the three dispatchers and for firm.pipeline static against dynamic,
// on a stream of one message type (predictable) and on a random mix of four (unpredictable).
// Output: design,one_type,mixed
#include <algorithm>
#include <chrono>
#include <cstdio>
#include <random>
#include <vector>

#include "firm_pipeline.hpp"
#include "firm_ubench.hpp"
#include "ll_dispatch.hpp"

using namespace ll::dispatch;
using sc = std::chrono::steady_clock;

template <class F>
double ns_per(F&& f, std::size_t n) {
    double best = 1e300;
    for (int r = 0; r < 15; ++r) {
        const auto t0 = sc::now();
        f();
        best = std::min(best, std::chrono::duration<double, std::nano>(sc::now() - t0).count() / static_cast<double>(n));
    }
    return best;
}

struct Ev { std::int64_t price; std::uint32_t qty; std::int64_t acc = 0; };
struct S1 { bool on(Ev& e) { e.acc += e.qty; return true; } };
struct S2 { bool on(Ev& e) { e.acc ^= e.price; return true; } };
struct S3 { std::int64_t limit; bool on(Ev& e) { return e.price < limit; } };
struct S4 { std::int64_t sum = 0; bool on(Ev& e) { sum += e.acc; return true; } };

int main() {
    constexpr std::size_t n = 1 << 16;
    std::mt19937 rng(4);
    std::vector<Msg> one(n), mix(n);
    std::vector<VarMsg> vone(n), vmix(n);
    for (std::size_t i = 0; i < n; ++i) {
        const auto q = static_cast<std::uint32_t>(rng() % 500 + 1);
        const auto p = static_cast<std::int64_t>(rng() % 1000);
        const auto t = static_cast<std::uint8_t>(rng() % 4);
        one[i] = {kAdd, q, p};
        mix[i] = {t, q, p};
        vone[i] = AddMsg{q};
        vmix[i] = t == kAdd ? VarMsg{AddMsg{q}} : t == kCancel ? VarMsg{CancelMsg{q}} : t == kExec ? VarMsg{ExecMsg{q}} : VarMsg{TradeMsg{q, p}};
    }
    State s;
    VirtualDispatch vd;
    Book bk;
    std::printf("design,one_type,mixed\n");
    auto row = [&](const char* name, auto run) { std::printf("%s,%.3f,%.3f\n", name, ns_per([&] { run(one, vone); }, n), ns_per([&] { run(mix, vmix); }, n)); };
    row("virtual", [&](auto& m, auto&) { for (const auto& x : m) vd.on(x, s); });
    row("variant", [&](auto&, auto& v) { for (const auto& x : v) on_variant(x, s); });
    row("CRTP", [&](auto& m, auto&) { for (const auto& x : m) bk.on(x, s); });
    firm::pipeline::Pipeline<Ev, S1, S2, S3, S4> sp(S1{}, S2{}, S3{900}, S4{});
    firm::pipeline::DynPipeline<Ev> dp;
    dp.add(S1{}); dp.add(S2{}); dp.add(S3{900}); dp.add(S4{});
    std::vector<Ev> ev(n);
    for (std::size_t i = 0; i < n; ++i) ev[i] = {mix[i].price, mix[i].qty};
    const double st = ns_per([&] { for (auto e : ev) sp.on(e); }, n);
    const double dy = ns_per([&] { for (auto e : ev) dp.on(e); }, n);
    std::printf("pipeline static,%.3f,%.3f\npipeline dynamic,%.3f,%.3f\n", st, st, dy, dy);
    firm::ubench::do_not_optimize(s);
    firm::ubench::do_not_optimize(sp.stage<3>().sum);
    return 0;
}
