#include "sum.hpp"

template <class T>
T total(const std::vector<T>& v) {
    T s{};
    for (const T& x : v) s += x;
    return s;
}
