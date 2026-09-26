// Acceptance test of firm.pipeline: order, short-circuit, and equality of the static and dynamic pipelines.
#include "firm_pipeline.hpp"

#include <cstdio>

using namespace firm::pipeline;

struct Ev { int x = 0; int trace = 0; };
struct Add { int k; bool on(Ev& e) { e.x += k; e.trace = e.trace * 10 + 1; return true; } };
struct Mul { int k; bool on(Ev& e) { e.x *= k; e.trace = e.trace * 10 + 2; return true; } };
struct Gate { int limit; bool on(Ev& e) { e.trace = e.trace * 10 + 3; return e.x <= limit; } };
static_assert(Stage<Add, Ev> && Stage<Gate, Ev>);

int main() {
    Pipeline<Ev, Add, Mul, Gate, Add> p(Add{1}, Mul{3}, Gate{10}, Add{100});
    DynPipeline<Ev> d;
    d.add(Add{1}); d.add(Mul{3}); d.add(Gate{10}); d.add(Add{100});
    for (int x = 0; x < 6; ++x) {
        Ev a{x, 0}, b{x, 0};
        const bool ra = p.on(a), rb = d.on(b);
        if (ra != rb || a.x != b.x || a.trace != b.trace) { std::puts("static and dynamic differ"); return 1; }
        const bool pass = (x + 1) * 3 <= 10;
        if (ra != pass || a.trace != (pass ? 1231 : 123)) { std::puts("order or short-circuit wrong"); return 1; }
    }
    std::puts("pipeline ok");
    return 0;
}
