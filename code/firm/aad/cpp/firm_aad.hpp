// firm.aad (C++20): algorithmic differentiation of the miniature firm. One Quant Book 4, ch. 28.
// Reverse (adjoint) mode on a thread-local tape by operator overloading, and forward mode by dual numbers. The same
// recording rules as firm_aad.py and the Rust crate; the pricing library and risk engine of later books use it.
#pragma once
#include <cmath>
#include <cstddef>
#include <numbers>
#include <vector>

namespace firm::aad {

// one recorded operation: up to two inputs and the local partial derivatives with respect to them
struct Node {
    int a = -1, b = -1;
    double da = 0.0, db = 0.0;
};

struct Tape {
    std::vector<Node> nodes;
    std::vector<double> adj;
    int push(int a, double da, int b = -1, double db = 0.0) {
        nodes.push_back({a, b, da, db});
        return static_cast<int>(nodes.size()) - 1;
    }
    // one reverse sweep from `out`: adj[j] = sum over the uses i of j of adj[i] * d v_i / d v_j
    void reverse(int out) {
        adj.assign(nodes.size(), 0.0);
        adj[out] = 1.0;
        for (int i = out; i >= 0; --i) {
            const Node& n = nodes[i];
            const double w = adj[i];
            if (w == 0.0) continue;
            if (n.a >= 0) adj[n.a] += w * n.da;
            if (n.b >= 0) adj[n.b] += w * n.db;
        }
    }
    void clear() { nodes.clear(); adj.clear(); }
};

inline thread_local Tape tape;

struct Var {
    int idx;
    double v;
    Var(double x = 0.0) : idx(tape.push(-1, 0.0)), v(x) {}  // an input (or a constant promoted to a node)
    Var(int i, double x) : idx(i), v(x) {}
    double adjoint() const { return tape.adj[idx]; }
};

inline Var operator+(Var x, Var y) { return {tape.push(x.idx, 1.0, y.idx, 1.0), x.v + y.v}; }
inline Var operator-(Var x, Var y) { return {tape.push(x.idx, 1.0, y.idx, -1.0), x.v - y.v}; }
inline Var operator*(Var x, Var y) { return {tape.push(x.idx, y.v, y.idx, x.v), x.v * y.v}; }
inline Var operator/(Var x, Var y) { return {tape.push(x.idx, 1.0 / y.v, y.idx, -x.v / (y.v * y.v)), x.v / y.v}; }
inline Var operator+(Var x, double c) { return {tape.push(x.idx, 1.0), x.v + c}; }
inline Var operator+(double c, Var x) { return x + c; }
inline Var operator-(Var x, double c) { return {tape.push(x.idx, 1.0), x.v - c}; }
inline Var operator-(double c, Var x) { return {tape.push(x.idx, -1.0), c - x.v}; }
inline Var operator*(Var x, double c) { return {tape.push(x.idx, c), x.v * c}; }
inline Var operator*(double c, Var x) { return x * c; }
inline Var operator/(Var x, double c) { return {tape.push(x.idx, 1.0 / c), x.v / c}; }
inline Var operator-(Var x) { return {tape.push(x.idx, -1.0), -x.v}; }
inline Var exp(Var x) { const double e = std::exp(x.v); return {tape.push(x.idx, e), e}; }
inline Var log(Var x) { return {tape.push(x.idx, 1.0 / x.v), std::log(x.v)}; }
inline Var sqrt(Var x) { const double s = std::sqrt(x.v); return {tape.push(x.idx, 0.5 / s), s}; }
inline double ncdf(double x) { return 0.5 * std::erfc(-x / std::numbers::sqrt2); }
inline Var ncdf(Var x) {
    return {tape.push(x.idx, std::exp(-0.5 * x.v * x.v) / std::sqrt(2 * std::numbers::pi)), ncdf(x.v)};
}

// forward mode: a value and one tangent
struct Dual {
    double v, d;
};
inline Dual operator+(Dual x, Dual y) { return {x.v + y.v, x.d + y.d}; }
inline Dual operator-(Dual x, Dual y) { return {x.v - y.v, x.d - y.d}; }
inline Dual operator*(Dual x, Dual y) { return {x.v * y.v, x.d * y.v + x.v * y.d}; }
inline Dual operator/(Dual x, Dual y) { return {x.v / y.v, (x.d * y.v - x.v * y.d) / (y.v * y.v)}; }
inline Dual operator+(Dual x, double c) { return {x.v + c, x.d}; }
inline Dual operator-(Dual x, double c) { return {x.v - c, x.d}; }
inline Dual operator*(Dual x, double c) { return {x.v * c, x.d * c}; }
inline Dual operator*(double c, Dual x) { return x * c; }
inline Dual operator/(Dual x, double c) { return {x.v / c, x.d / c}; }
inline Dual operator-(Dual x) { return {-x.v, -x.d}; }
inline Dual exp(Dual x) { const double e = std::exp(x.v); return {e, e * x.d}; }
inline Dual log(Dual x) { return {std::log(x.v), x.d / x.v}; }
inline Dual ncdf(Dual x) { return {ncdf(x.v), std::exp(-0.5 * x.v * x.v) / std::sqrt(2 * std::numbers::pi) * x.d}; }

}  // namespace firm::aad
