#include <algorithm>
#include <cstddef>
#include <utility>

class Buffer {
    std::size_t n_ = 0;
    double* data_ = nullptr;

public:
    explicit Buffer(std::size_t n) : n_(n), data_(new double[n]{}) {}
    ~Buffer() { delete[] data_; }
    Buffer(const Buffer& o) : n_(o.n_), data_(new double[o.n_]) {
        std::copy(o.data_, o.data_ + n_, data_);
    }
    Buffer(Buffer&& o) noexcept
        : n_(std::exchange(o.n_, 0)), data_(std::exchange(o.data_, nullptr)) {}
    Buffer& operator=(Buffer o) noexcept {       // by value: serves copy and move
        std::swap(n_, o.n_);
        std::swap(data_, o.data_);
        return *this;
    }
    double& operator[](std::size_t i) { return data_[i]; }
    std::size_t size() const { return n_; }
};
// Not printed: the check.
#include <iostream>
int main() {
    Buffer a(4);
    {
        Buffer b = a;
        b[0] = 1.0;
    }
    a[0] = 2.0;
    Buffer c(1);
    c = a;
    c[1] = 5.0;
    Buffer d = std::move(c);
    a = a;
    std::cout << a[0] << " " << a[1] << " " << d[1] << " " << c.size() << "\n";
}
