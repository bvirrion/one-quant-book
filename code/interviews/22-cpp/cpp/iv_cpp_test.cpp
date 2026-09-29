// Tests for iv_cpp.hpp (built by tools/test_code.sh with -std=c++20 -O2 -Wall -Wextra -Werror).
#include <cassert>
#include <cstdio>
#include <random>
#include <deque>

#include "iv_cpp.hpp"

struct Order {
    std::int64_t price;
    std::int64_t qty;
};
struct NotAnOrder {
    double px;
};

static_assert(iv::kPow10[0] == 1 && iv::kPow10[6] == 1'000'000 && iv::kPow10[18] == 1'000'000'000'000'000'000);
static_assert(iv::OrderLike<Order>);
static_assert(!iv::OrderLike<NotAnOrder>);
static_assert(iv::notional(Order{1025, 300}) == 307'500);
static_assert(std::is_nothrow_move_constructible_v<iv::Buffer>);
static_assert(std::is_nothrow_move_assignable_v<iv::Buffer>);

int main() {
    iv::Buffer a(4);
    a[0] = 7;
    iv::Buffer b = std::move(a);
    assert(a.size() == 0 && b.size() == 4 && b[0] == 7);
    iv::Buffer c(1);
    c = std::move(b);
    assert(b.size() == 0 && c.size() == 4 && c[0] == 7);
    iv::Buffer d(c);
    d[0] = 9;
    assert(c[0] == 7 && d[0] == 9);
    c = d;
    assert(c[0] == 9);
    c = c;  // self-assignment is safe
    assert(c[0] == 9);

    iv::RingBuffer<int, 8> rb;
    std::deque<int> model;
    std::mt19937 rng(7);
    for (int step = 0; step < 100000; ++step) {
        if (rng() % 2) {
            const int v = static_cast<int>(rng() % 1000);
            const bool ok = rb.push(v);
            assert(ok == (model.size() < 8));
            if (ok) model.push_back(v);
        } else {
            const auto v = rb.pop();
            assert(v.has_value() == !model.empty());
            if (v) {
                assert(*v == model.front());
                model.pop_front();
            }
        }
        assert(rb.size() == model.size());
    }
    std::puts("iv_cpp_test: all passed");
    return 0;
}
