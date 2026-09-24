#include "firm_auction.hpp"
#include <cassert>
#include <map>

using firm::AuctionOrder;

int main() {
    const std::vector<AuctionOrder> book{
        {"b1", +1, 300, std::nullopt, 1}, {"b2", +1, 500, 1003, 2}, {"b3", +1, 400, 1001, 3}, {"b4", +1, 600, 1000, 4},
        {"s1", -1, 200, std::nullopt, 5}, {"s2", -1, 400, 999, 6}, {"s3", -1, 500, 1001, 7}, {"s4", -1, 700, 1002, 8}};
    const auto u = firm::uncross(book, 1000);
    assert(u.price && *u.price == 1001 && u.volume == 1100 && u.surplus == 100);
    std::map<std::string, std::int64_t> f(u.fills.begin(), u.fills.end());
    assert(f["b1"] == 300 && f["b2"] == 500 && f["b3"] == 300 && f["s3"] == 500 && !f.count("s4"));

    assert(!firm::uncross({{"b", +1, 100, 990, 1}, {"s", -1, 100, 1010, 2}}, 1000).price);
    assert(*firm::uncross({{"b", +1, 500, 1005, 1}, {"s", -1, 200, 1000, 2}}, 1002).price == 1005);
    assert(*firm::uncross({{"b", +1, 200, 1005, 1}, {"s", -1, 500, 1000, 2}}, 1002).price == 1000);
    assert(*firm::uncross({{"b", +1, 300, 1006, 1}, {"s", -1, 300, 1000, 2}}, 1004).price == 1004);
    const auto t = firm::uncross({{"early", +1, 300, 1000, 1}, {"late", +1, 300, 1000, 2}, {"s", -1, 400, 1000, 3}}, 1000);
    std::map<std::string, std::int64_t> g(t.fills.begin(), t.fills.end());
    assert(g["early"] == 300 && g["late"] == 100 && g["s"] == 400);
    return 0;
}
