// Chapter 7 of One Quant Book 13: three ways to dispatch a market-data message to its handler, a table computed at
// compile time, and an error path kept out of the hot path.
#pragma once
#include <array>
#include <cstdint>
#include <cstdio>
#include <variant>

namespace ll::dispatch {

enum Type : std::uint8_t { kAdd, kCancel, kExec, kTrade };
struct Msg { std::uint8_t type; std::uint32_t qty; std::int64_t price; };
struct State { std::int64_t added = 0, cancelled = 0, executed = 0, notional = 0; };

// 1. Dynamic dispatch: one handler object per type behind a base class.
struct Handler { virtual ~Handler() = default; virtual void on(const Msg& m, State& s) = 0; };
struct OnAdd final : Handler { void on(const Msg& m, State& s) override { s.added += m.qty; } };
struct OnCancel final : Handler { void on(const Msg& m, State& s) override { s.cancelled += m.qty; } };
struct OnExec final : Handler { void on(const Msg& m, State& s) override { s.executed += m.qty; } };
struct OnTrade final : Handler { void on(const Msg& m, State& s) override { s.notional += m.price * m.qty; } };

struct VirtualDispatch {
    OnAdd a; OnCancel c; OnExec e; OnTrade t;
    std::array<Handler*, 4> table{&a, &c, &e, &t};
    void on(const Msg& m, State& s) { table[m.type]->on(m, s); }
};

// 2. A closed set of alternatives: std::variant and std::visit.
struct AddMsg { std::uint32_t qty; };
struct CancelMsg { std::uint32_t qty; };
struct ExecMsg { std::uint32_t qty; };
struct TradeMsg { std::uint32_t qty; std::int64_t price; };
using VarMsg = std::variant<AddMsg, CancelMsg, ExecMsg, TradeMsg>;
template <class... F> struct Overload : F... { using F::operator()...; };
template <class... F> Overload(F...) -> Overload<F...>;

inline void on_variant(const VarMsg& m, State& s) {
    std::visit(Overload{[&](const AddMsg& x) { s.added += x.qty; },
                        [&](const CancelMsg& x) { s.cancelled += x.qty; },
                        [&](const ExecMsg& x) { s.executed += x.qty; },
                        [&](const TradeMsg& x) { s.notional += x.price * x.qty; }},
               m);
}

// 3. Static polymorphism with the curiously recurring template pattern: the base knows the derived type at compile
// time, so every handler call is direct and can be inlined.
template <class Derived>
struct StaticDispatch {
    void on(const Msg& m, State& s) {
        auto& d = static_cast<Derived&>(*this);
        switch (m.type) {
            case kAdd: d.on_add(m, s); break;
            case kCancel: d.on_cancel(m, s); break;
            case kExec: d.on_exec(m, s); break;
            default: d.on_trade(m, s); break;
        }
    }
};
struct Book : StaticDispatch<Book> {
    void on_add(const Msg& m, State& s) { s.added += m.qty; }
    void on_cancel(const Msg& m, State& s) { s.cancelled += m.qty; }
    void on_exec(const Msg& m, State& s) { s.executed += m.qty; }
    void on_trade(const Msg& m, State& s) { s.notional += m.price * m.qty; }
};

// A table computed by the compiler: powers of ten for scaling prices with up to 18 implied decimals.
consteval std::array<std::int64_t, 19> make_pow10() {
    std::array<std::int64_t, 19> t{};
    t[0] = 1;
    for (std::size_t i = 1; i < t.size(); ++i) t[i] = t[i - 1] * 10;
    return t;
}
inline constexpr auto kPow10 = make_pow10();
static_assert(kPow10[4] == 10'000 && kPow10[18] == 1'000'000'000'000'000'000);

// The rare path, out of line: the hot function keeps only a predicted-not-taken branch and a call.
[[gnu::cold, gnu::noinline]] inline void report_bad_scale(int scale) { std::fprintf(stderr, "bad price scale %d\n", scale); }

inline std::int64_t rescale(std::int64_t price, int from, int to) {
    if (from < 0 || from > 18 || to < 0 || to > 18) [[unlikely]] {
        report_bad_scale(from < 0 || from > 18 ? from : to);
        return 0;
    }
    return to >= from ? price * kPow10[static_cast<std::size_t>(to - from)] : price / kPow10[static_cast<std::size_t>(from - to)];
}

}  // namespace ll::dispatch
