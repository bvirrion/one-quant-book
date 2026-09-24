// Acceptance tests of firm.ratelimit (C++20): the same cases as the Python reference.
#include "firm_ratelimit.hpp"
#include <cassert>

using namespace firm::ratelimit;

int main() {
    {
        Governor g({{Kind::weight, 60'000, 100}});
        assert(g.try_send(1'000, 60, false) == std::make_pair(true, std::int64_t{0}));
        assert(g.try_send(2'000, 50, false) == std::make_pair(false, std::int64_t{58'000}));
        assert(g.try_send(60'000, 50, false) == std::make_pair(true, std::int64_t{0}));
    }
    {
        Governor g = binance_like();
        for (std::int64_t i = 0; i < 100; ++i) assert(g.try_send(i, 1, true).first);
        assert(g.try_send(100, 1, true) == std::make_pair(false, std::int64_t{9'900}));
        assert(g.try_send(100, 1, false) == std::make_pair(true, std::int64_t{0}));
    }
    {
        Governor g = binance_like();
        g.on_status(5'000, 429, 3'000);
        assert(g.try_send(6'000, 1, false) == std::make_pair(false, std::int64_t{2'000}));
        g.on_status(9'000, 418, 120'000);
        assert(g.try_send(100'000, 1, false) == std::make_pair(false, std::int64_t{29'000}));
        assert(g.log().size() == 2 && g.log()[0] == "429@5000" && g.log()[1] == "418@9000");
    }
    return 0;
}
