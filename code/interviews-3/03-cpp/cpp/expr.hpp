#pragma once
#include <concepts>
#include <cstddef>
#include <vector>

template <class E>
concept Expr = requires(const E& e, std::size_t i) {
    { e[i] } -> std::convertible_to<double>;
    { e.size() } -> std::convertible_to<std::size_t>;
};

template <Expr L, Expr R>
struct Add {
    const L& l;                                 // references: cheap, and the trap
    const R& r;
    double operator[](std::size_t i) const { return l[i] + r[i]; }
    std::size_t size() const { return l.size(); }
};

template <Expr L, Expr R>
Add<L, R> operator+(const L& l, const R& r) { return {l, r}; }

class Vector {
    std::vector<double> d_;

public:
    explicit Vector(std::size_t n, double v = 0) : d_(n, v) {}
    template <Expr E>
    Vector(const E& e) : d_(e.size()) { assign(e); }
    template <Expr E>
    Vector& operator=(const E& e) { assign(e); return *this; }
    double operator[](std::size_t i) const { return d_[i]; }
    double& operator[](std::size_t i) { return d_[i]; }
    std::size_t size() const { return d_.size(); }

private:
    template <class E>
    void assign(const E& e) {
        for (std::size_t i = 0; i < size(); ++i) d_[i] = e[i];   // one loop, no temporaries
    }
};
