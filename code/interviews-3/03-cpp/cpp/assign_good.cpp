#include <algorithm>
#include <cstddef>
#include <new>
#include <utility>

static bool fail_next = false;
int* get(std::size_t n) {
    if (fail_next) throw std::bad_alloc{};
    return new int[n]{};
}

class Buf {
    std::size_t n_;
    int* d_;

public:
    explicit Buf(std::size_t n) : n_(n), d_(get(n)) {}
    Buf(const Buf& o) : n_(o.n_), d_(get(o.n_)) { std::copy(o.d_, o.d_ + n_, d_); }
    ~Buf() { delete[] d_; }
    friend void swap(Buf& a, Buf& b) noexcept {
        std::swap(a.n_, b.n_);
        std::swap(a.d_, b.d_);
    }
    Buf& operator=(const Buf& o) {
        Buf copy(o);                             // may throw; *this is untouched
        swap(*this, copy);                       // cannot throw
        return *this;
    }
    int& operator[](std::size_t i) { return d_[i]; }
};
// Not printed: the two checks.
#include <iostream>
int main() {
    Buf a(3), b(3);
    a[0] = 7;
    b[0] = 8;
    Buf& same = a;
    a = same;
    std::cout << a[0] << "\n";
    fail_next = true;
    try {
        a = b;
    } catch (const std::bad_alloc&) {
        std::cout << "caught " << a[0] << "\n";
    }
    fail_next = false;
    a = b;
    std::cout << a[0] << "\n";
}
