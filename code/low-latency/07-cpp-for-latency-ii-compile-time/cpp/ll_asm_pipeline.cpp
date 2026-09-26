// Chapter 7: two functions compiled to assembly for the book (python/asm_pipeline.py). The static pipeline's calls are
// all inlined; the dynamic one keeps an indirect call per stage.
#include "../../../firm/pipeline/cpp/firm_pipeline.hpp"

struct Ev { long price; unsigned qty; long acc; };
struct S1 { bool on(Ev& e) { e.acc += e.qty; return true; } };
struct S2 { bool on(Ev& e) { e.acc ^= e.price; return true; } };
struct S3 { long limit; bool on(Ev& e) { return e.price < limit; } };
struct S4 { long sum = 0; bool on(Ev& e) { sum += e.acc; return true; } };

using Static = firm::pipeline::Pipeline<Ev, S1, S2, S3, S4>;
using Dynamic = firm::pipeline::DynPipeline<Ev>;

extern "C" bool run_static(Static& p, Ev& e) { return p.on(e); }
extern "C" bool run_dynamic(Dynamic& p, Ev& e) { return p.on(e); }
