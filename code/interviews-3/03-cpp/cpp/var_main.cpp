#include "var.hpp"
#include <cstdint>
#include <cstdio>
#include <random>
#include <stdexcept>
#include <string>
#include <variant>

struct C {
    static inline int live = 0, boom = 0;
    std::string s;
    explicit C(std::string v) : s(std::move(v)) { if (boom) throw std::runtime_error("x"); ++live; }
    C(const C& o) : s(o.s) { ++live; }
    ~C() { --live; }
};
struct alignas(32) Wide { long x; };
using V = Var<int, C, Wide>;
static_assert(alignof(V) == 32);

struct Visit {
    long operator()(int i) const { return i; }
    long operator()(const C& c) const { return long(c.s.size()) + 1000; }
    long operator()(const Wide& w) const { return w.x + 2000; }
};

int main() {
    std::mt19937 g(2);
    {
        V m;
        std::variant<std::monostate, int, C, Wide> t;
        for (int i = 0; i < 30000; ++i) {
            int v = g() % 50;
            switch (g() % 4) {
                case 0: m.emplace<int>(v); t.emplace<int>(v); break;
                case 1: m.emplace<C>(std::string(v, 'x')); t.emplace<C>(std::string(v, 'x')); break;
                case 2: m.emplace<Wide>(Wide{v}); t.emplace<Wide>(Wide{v}); break;
                case 3:
                    C::boom = 1;
                    try { m.emplace<C>(std::string(v, 'x')); } catch (const std::runtime_error&) {}
                    C::boom = 0;
                    t.emplace<std::monostate>();
                    break;
            }
            if (m.valueless() != std::holds_alternative<std::monostate>(t)) { std::puts("state"); return 1; }
            if (!m.valueless()) {
                long want = std::visit([](const auto& x) -> long {
                    if constexpr (std::is_same_v<std::decay_t<decltype(x)>, std::monostate>) return 0;
                    else return Visit{}(x);
                }, t);
                if (m.visit(Visit{}) != want) { std::puts("visit"); return 1; }
            }
            if (C::live != int(std::holds_alternative<C>(t)) * 2) { std::puts("live"); return 1; }
            if (m.index() != (t.index() == 0 ? 3 : t.index() - 1)) { std::puts("index"); return 1; }
        }
    }
    V w;
    Wide& r = w.emplace<Wide>(Wide{1});
    std::printf("%d %d %d\n", C::live, int(reinterpret_cast<std::uintptr_t>(&r) % 32), w.get_if<int>() == nullptr);
}
