#include <cstddef>
#include <iostream>
#include <string>
#include <utility>

template <class T>
class MiniVec {
    T* d_ = nullptr;
    std::size_t n_ = 0, cap_ = 0;

    void grow() {
        std::size_t c = cap_ ? 2 * cap_ : 1;
        T* fresh = new T[c];
        for (std::size_t i = 0; i < n_; ++i) fresh[i] = std::move(d_[i]);
        delete[] d_;
        d_ = fresh;
        cap_ = c;
    }

public:
    MiniVec() = default;
    MiniVec(const MiniVec&) = delete;
    ~MiniVec() { delete[] d_; }
    void push_back(const T& x) {
        if (n_ == cap_) grow();
        d_[n_++] = x;
    }
    T& operator[](std::size_t i) { return d_[i]; }
    std::size_t size() const { return n_; }
};

int main() {
    MiniVec<std::string> v;
    v.push_back(std::string(40, 'x'));
    v.push_back(v[0]);
    std::cout << v.size() << " " << v[1].size() << "\n";
}
