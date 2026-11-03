#include "opt.hpp"
#include <cstdint>
#include <cstdio>
#include <optional>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

struct C {
    static inline int live = 0, boom = -1;
    std::string v;
    explicit C(const std::string& s) : v(s) { if (boom == 0) { boom = -1; throw std::runtime_error("x"); } --boom; ++live; }
    C(const C& o) : v(o.v) { ++live; }
    C(C&& o) noexcept : v(std::move(o.v)) { ++live; }
    C& operator=(const C&) = default;
    C& operator=(C&&) noexcept = default;
    ~C() { --live; }
};
struct alignas(64) Wide { char c = 'w'; };

int main() {
    std::mt19937 g(9);
    std::vector<Opt<C>> m(4);
    std::vector<std::optional<C>> t(4);
    for (int i = 0; i < 20000; ++i) {
        int a = g() % 4, b = g() % 4;
        std::string s(g() % 40, 'x');
        switch (g() % 5) {
            case 0: m[a].emplace(s); t[a].emplace(s); break;
            case 1: m[a].reset(); t[a].reset(); break;
            case 2: m[a] = m[b]; t[a] = t[b]; break;
            case 3: if (a != b) { m[a] = std::move(m[b]); t[a] = std::move(t[b]); } break;
            case 4: {
                C::boom = 0;
                try { m[a].emplace(s); } catch (const std::runtime_error&) {}
                t[a].reset();
                C::boom = -1;
                break;
            }
        }
        for (int k = 0; k < 4; ++k) {
            if (bool(m[k]) != bool(t[k])) { std::puts("has"); return 1; }
            if (m[k] && (*m[k]).v != (*t[k]).v) { std::puts("value"); return 1; }
        }
    }
    m.clear();
    t.clear();
    Opt<Wide> w;
    w.emplace();
    std::printf("%d %d\n", C::live, int(reinterpret_cast<std::uintptr_t>(&*w) % 64));
}
