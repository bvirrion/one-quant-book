// Drives Book from standard input: "a id side price qty", "c id", each followed by a line "ok bidprice bidqty askprice askqty".
#include <cstdio>
#include <iostream>
#include <string>

#include "book.hpp"

int main() {
    Book book;
    std::string op;
    while (std::cin >> op) {
        long id = 0;
        std::cin >> id;
        bool ok = false;
        if (op == "a") {
            char side = 0;
            long price = 0, qty = 0;
            std::cin >> side >> price >> qty;
            ok = book.add(id, side == 'b' ? Side::Bid : Side::Ask, price, qty);
        } else {
            ok = book.cancel(id);
        }
        const auto b = book.best_bid();
        const auto a = book.best_ask();
        std::printf("%d %ld %ld %ld %ld\n", ok ? 1 : 0, b ? b->price : -1L, b ? b->qty : 0L, a ? a->price : -1L,
                    a ? a->qty : 0L);
    }
}
