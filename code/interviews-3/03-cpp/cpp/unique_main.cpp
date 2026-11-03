// Random operations on Unique against std::unique_ptr, comparing live counts and values.
#include "unique.hpp"
#include <cstdio>
#include <memory>
#include <random>
#include <type_traits>
#include <vector>

struct C {
    static inline int live = 0;
    int v;
    explicit C(int x) : v(x) { ++live; }
    ~C() { --live; }
};
static_assert(!std::is_copy_constructible_v<Unique<C>>);
static_assert(std::is_nothrow_move_constructible_v<Unique<C>>);
static_assert(sizeof(Unique<C>) == sizeof(C*));

int main() {
    std::mt19937 g(7);
    std::vector<Unique<C>> mine(5);
    std::vector<std::unique_ptr<C>> theirs(5);
    long steps = 0;
    for (int i = 0; i < 20000; ++i) {
        int a = g() % 5, b = g() % 5, x = g() % 1000;
        switch (g() % 5) {
            case 0: mine[a] = Unique<C>(new C(x)); theirs[a] = std::make_unique<C>(x); C::live--; C::live++; break;
            case 1: mine[a] = std::move(mine[b]); theirs[a] = std::move(theirs[b]); break;
            case 2: mine[a].reset(); theirs[a].reset(); break;
            case 3: { C* m = mine[a].release(); C* t = theirs[a].release(); delete m; delete t; break; }
            case 4: if (a != b) { std::swap(mine[a], mine[b]); std::swap(theirs[a], theirs[b]); } break;
        }
        for (int k = 0; k < 5; ++k) {
            if (bool(mine[k]) != bool(theirs[k])) { std::puts("mismatch"); return 1; }
            if (mine[k] && mine[k]->v != theirs[k]->v) { std::puts("value"); return 1; }
        }
        ++steps;
    }
    mine.clear();
    theirs.clear();
    std::printf("%ld %d\n", steps, C::live);
}
