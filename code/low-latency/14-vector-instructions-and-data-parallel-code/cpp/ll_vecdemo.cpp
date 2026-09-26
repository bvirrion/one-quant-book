// Chapter 14: loops for the compiler's vectorisation report (compiled with -c only; ll_vecreport.py runs it).
#include <cstddef>

#include "ll_simd.hpp"

using ll::simd::Move;
using ll::simd::OptionRow;

// The revaluation over columns, with pointers that may alias: the compiler must check at run time.
void reval_columns(const double* q, const double* d, const double* g, const double* v, const double* th, Move m,
                   double* out, std::size_t n) {
    const double h = 0.5 * m.dS * m.dS;
    for (std::size_t i = 0; i < n; ++i)
        out[i] = q[i] * (d[i] * m.dS + g[i] * h + v[i] * m.dvol + th[i] * m.dt);
}

// The same over 80-byte records: the five fields are 8 bytes apart inside a record, records 80 bytes apart.
void reval_rows(const OptionRow* r, Move m, double* out, std::size_t n) {
    const double h = 0.5 * m.dS * m.dS;
    for (std::size_t i = 0; i < n; ++i)
        out[i] = r[i].qty * (r[i].delta * m.dS + r[i].gamma * h + r[i].vega * m.dvol + r[i].theta * m.dt);
}

// A loop that may leave early: the search for a delimiter.
std::size_t find_first(const char* p, std::size_t n, char c) {
    for (std::size_t i = 0; i < n; ++i)
        if (p[i] == c) return i;
    return n;
}

// Reductions: integers may be summed in any order, doubles may not (without -ffast-math).
long sum_ints(const int* x, std::size_t n) {
    long s = 0;
    for (std::size_t i = 0; i < n; ++i) s += x[i];
    return s;
}

double sum_doubles(const double* x, std::size_t n) {
    double s = 0;
    for (std::size_t i = 0; i < n; ++i) s += x[i];
    return s;
}
