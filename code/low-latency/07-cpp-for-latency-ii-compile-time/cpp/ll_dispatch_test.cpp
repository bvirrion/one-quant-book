// Chapter 7: the three dispatchers compute the same state; the compile-time table and the cold path behave.
#include "ll_dispatch.hpp"

#include <random>
#include <vector>

using namespace ll::dispatch;

int main() {
    std::mt19937 rng(9);
    std::vector<Msg> ms;
    std::vector<VarMsg> vs;
    for (int i = 0; i < 10000; ++i) {
        Msg m{static_cast<std::uint8_t>(rng() % 4), static_cast<std::uint32_t>(rng() % 500 + 1), static_cast<std::int64_t>(rng() % 1000)};
        ms.push_back(m);
        switch (m.type) {
            case kAdd: vs.emplace_back(AddMsg{m.qty}); break;
            case kCancel: vs.emplace_back(CancelMsg{m.qty}); break;
            case kExec: vs.emplace_back(ExecMsg{m.qty}); break;
            default: vs.emplace_back(TradeMsg{m.qty, m.price}); break;
        }
    }
    State a, b, c;
    VirtualDispatch vd;
    Book bk;
    for (std::size_t i = 0; i < ms.size(); ++i) { vd.on(ms[i], a); on_variant(vs[i], b); bk.on(ms[i], c); }
    auto same = [](const State& x, const State& y) { return x.added == y.added && x.cancelled == y.cancelled && x.executed == y.executed && x.notional == y.notional; };
    if (!same(a, b) || !same(a, c) || a.added == 0) return 1;
    if (rescale(12345, 2, 4) != 1234500 || rescale(1234500, 4, 2) != 12345 || rescale(1, 19, 0) != 0) return 1;
    return 0;
}
