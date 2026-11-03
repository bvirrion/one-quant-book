#include <algorithm>
#include <cstddef>
#include <new>

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
    Buf& operator=(const Buf& o) {
        delete[] d_;
        n_ = o.n_;
        d_ = get(n_);
        std::copy(o.d_, o.d_ + n_, d_);
        return *this;
    }
    int& operator[](std::size_t i) { return d_[i]; }
};
// Not printed: the two failures.
#include <iostream>
int main(int argc, char**) {
    Buf a(3), b(3);
    a[0] = 7;
    if (argc == 1) {
        Buf& same = a;
        a = same;
        std::cout << a[0] << "\n";
    } else {
        fail_next = true;
        try {
            a = b;
        } catch (const std::bad_alloc&) {
            std::cout << "caught\n";
        }
        fail_next = false;
    }
}
