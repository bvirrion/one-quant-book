#include "firm_nbbo.hpp"
#include <cassert>

int main() {
    firm::NbboBuilder b;
    b.update(0, 100000, 300, 100200, 500);   // XNYS
    b.update(1, 100100, 200, 100200, 100);   // XNAS
    b.update(2, 100100, 400, 100300, 900);   // IEXG
    auto n = b.nbbo();
    assert(n && n->bid == 100100 && n->bid_size == 600 && n->bid_venues == 0b110u);
    assert(n->ask == 100200 && n->ask_size == 600 && n->ask_venues == 0b011u);
    assert(!b.update(3, 100150, 60, 100400, 100));             // odd lot: not protected
    assert(b.update(3, 100150, 100, 100400, 100)->bid == 100150);
    assert(b.trades_through(+1, 100300) && !b.trades_through(+1, 100200));
    assert(b.update(0, 100200, 300, 100300, 500)->locked());
    assert(b.update(0, 100250, 300, 100300, 500)->crossed());
    bool threw = false;
    try { b.update(99, 1, 1, 1, 1); } catch (const std::invalid_argument&) { threw = true; }
    assert(threw);
    return threw ? 0 : 1;
}
