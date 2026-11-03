// Drives a Side from standard input: "a price id qty", "c id", "t qty", printing "ok-or-filled best" after each.
// Compile with -DFIXED for the corrected class, which orders bids by std::greater when given -DBID.
#include <cstdio>
#include <functional>
#include <iostream>
#include <iterator>
#include <string>

#ifdef FIXED
#include "book_fixed.hpp"
#ifdef BID
using TheSide = Side<std::greater<long>>;
#else
using TheSide = Side<std::less<long>>;
#endif
#else
#include "book_bugs.hpp"
using TheSide = Side;
#endif

int main() {
    TheSide side;
    std::string op;
    while (std::cin >> op) {
        long out = 0;
        if (op == "a") {
            long price = 0, id = 0, qty = 0;
            std::cin >> price >> id >> qty;
            side.add(price, id, qty);
        } else if (op == "c") {
            long id = 0;
            std::cin >> id;
            out = side.cancel(id) ? 1 : 0;
        } else {
            long qty = 0;
            std::cin >> qty;
            out = side.take(qty);
        }
        std::printf("%ld %ld\n", out, side.empty() ? -1L : side.best());
    }
}
