// Acceptance tests of firm.wsbook (C++20): the same cases as the Python reference.
#include "firm_wsbook.hpp"
#include <cassert>

using namespace firm::wsbook;

static Book book() {
    Book b;
    b.snapshot(100, {{999, 5}, {998, 7}}, {{1001, 4}, {1002, 6}});
    return b;
}

int main() {
    {
        Book b = book();
        assert(b.apply(95, 100, {{999, 1}}, {}) == Status::ignored);
        assert(b.apply(99, 101, {{999, 0}}, {{1001, 9}}) == Status::applied);
        assert(b.bids().size() == 1 && b.bids().at(998) == 7 && b.asks().at(1001) == 9 && b.update_id() == 101);
        assert(b.apply(103, 104, {}, {{1003, 1}}) == Status::gap && !b.synced());
        assert(b.apply(105, 105, {}, {}) == Status::gap);
    }
    {
        Book b = book();
        assert(b.checksum() == 3348617501u);            // zlib.crc32 of "10014" "10026" "9995" "9987"
        assert(crc32("123456789") == 0xCBF43926u);
    }
    return 0;
}
