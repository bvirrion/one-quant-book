// Chapter 8: undefined behaviour as a contract the optimiser relies on. Compiled to assembly by python/ll_ub.py.
#include <climits>

// Signed overflow is undefined, so x + 1 > x is always true for the optimiser.
extern "C" bool plus_one_greater(int x) { return x + 1 > x; }

// The pattern of the 2009 kernel bug: the pointer is dereferenced, then checked; the check is deleted.
extern "C" int first_then_check(const int* p) {
    const int v = *p;
    if (!p) return -1;
    return v;
}

// Strict aliasing: an int and a float are assumed never to share an address.
extern "C" int alias(int* i, float* f) {
    *i = 1;
    *f = 0.0f;
    return *i;
}
