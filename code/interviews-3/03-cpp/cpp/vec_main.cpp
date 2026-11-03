#include "vec.hpp"
#include <cstdio>
#include <memory>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

struct C {
    static inline int live = 0, boom = -1;
    std::string v;
    static void tick() { if (boom == 0) { boom = -1; throw std::runtime_error("x"); } if (boom > 0) --boom; }
    explicit C(const std::string& s) : v(s) { tick(); ++live; }
    C(const C& o) : v(o.v) { tick(); ++live; }
    C(C&& o) : v(std::move(o.v)) { tick(); ++live; }    // a move that may throw: the vector must copy
    C& operator=(const C&) = delete;
    ~C() { --live; }
};

template <class V> std::string dump(const V& x) {
    std::string s;
    for (std::size_t i = 0; i < x.size(); ++i) s += x[i].v + ",";
    return s;
}

int main() {
    std::mt19937 g(5);
    {
        Vec<C> m;
        std::vector<std::string> t;
        for (int i = 0; i < 20000; ++i) {
            std::string s(g() % 40, char('a' + g() % 26));
            switch (g() % 5) {
                case 0: case 1:
                    m.emplace_back(s); t.push_back(s); break;
                case 2:
                    if (!t.empty()) { m.pop_back(); t.pop_back(); } break;
                case 3: {                                  // a throw somewhere inside the growth
                    std::string before = dump(m);
                    std::size_t cap = m.capacity();
                    C::boom = int(g() % (m.size() + 2));
                    try {
                        m.emplace_back(s);
                        t.push_back(s);
                    } catch (const std::runtime_error&) {
                        if (dump(m) != before || m.capacity() != cap) { std::puts("guarantee"); return 1; }
                    }
                    C::boom = -1;
                    break;
                }
                case 4: {
                    Vec<C> copy = m;
                    m = std::move(copy);
                    if (!t.empty() && g() % 50 == 0) { m = Vec<C>{}; t.clear(); }
                    break;
                }
            }
            if (m.size() != t.size()) { std::puts("size"); return 1; }
            for (std::size_t k = 0; k < t.size(); ++k)
                if (m[k].v != t[k]) { std::puts("value"); return 1; }
            if (std::size_t(C::live) != t.size()) { std::puts("live"); return 1; }
            if (t.size() > 60) { m = Vec<C>{}; t.clear(); }
        }
    }
    Vec<std::string> self;
    self.emplace_back(40, 'x');
    for (int i = 0; i < 40; ++i) self.emplace_back(self[0]);      // an element of itself
    Vec<std::unique_ptr<int>> only;
    for (int i = 0; i < 40; ++i) only.emplace_back(std::make_unique<int>(i));
    std::printf("%d %zu %zu %d\n", C::live, self.size(), self[40].size(), *only[39]);
}
