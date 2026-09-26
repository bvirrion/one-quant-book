// Chapter 1: the toy path is correct before it is timed.
#include "ll_path.hpp"

#include <cstdio>
#include <fstream>
#include <iterator>
#include <vector>

int main() {
    std::ifstream f("code/firm/feed/data/sample.itch", std::ios::binary);
    const std::vector<std::uint8_t> data{std::istreambuf_iterator<char>(f), std::istreambuf_iterator<char>()};
    firm::feed::Book book;
    ll::path::Decider d;
    std::size_t i = 0, n = 0;
    std::array<std::uint8_t, 64> buf{};
    while (i < data.size()) {
        const std::size_t len = (static_cast<std::size_t>(data[i]) << 8) | data[i + 1];
        const auto m = ll::path::decode_one(std::span(data).subspan(i, len + 2));
        book.apply(m);
        if (d.on(m) && ll::path::encode_order(buf, n, 'B', 100, m.locate, m.price) != 47) return 1;
        i += len + 2;
        ++n;
    }
    if (n != 2020 || book.errors() != 0 || d.sent == 0 || buf[0] != 'O') { std::printf("path failed: n=%zu errors=%llu sent=%llu\n", n, static_cast<unsigned long long>(book.errors()), static_cast<unsigned long long>(d.sent)); return 1; }
    std::printf("path ok: %zu messages, %llu orders\n", n, static_cast<unsigned long long>(d.sent));
    return 0;
}
