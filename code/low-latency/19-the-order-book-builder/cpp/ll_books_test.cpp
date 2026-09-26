// Chapter 19: the tree and sorted-vector builders agree with the ladder, level 2 after every event, on both fixtures.
#include "ll_books.hpp"

#include <cstdio>
#include <fstream>
#include <iterator>
#include <string>

static std::vector<firm::feed2::Event> events(const std::string& name) {
    std::ifstream f("code/firm/bookbuilder/data/" + name + ".bin", std::ios::binary);
    const std::vector<std::uint8_t> b{std::istreambuf_iterator<char>(f), {}};
    std::vector<firm::feed2::Event> out;
    for (std::size_t i = 0; i + 48 <= b.size(); i += 48) {
        firm::feed2::Event e;
        e.kind = b[i];
        e.side = b[i + 1];
        std::memcpy(&e.ref, &b[i + 20], 8);
        std::memcpy(&e.ref2, &b[i + 28], 8);
        std::memcpy(&e.price, &b[i + 36], 4);
        std::memcpy(&e.qty, &b[i + 40], 8);
        out.push_back(e);
    }
    return out;
}

int main() {
    int fails = 0;
    for (const std::string name : {"events_sim", "events_small"}) {
        const auto ev = events(name);
        firm::book::LadderBook ladder(name == "events_sim" ? 100 : 1);
        ll::books::TreeBook tree;
        ll::books::VecBook vec;
        std::uint64_t h0 = 0xCBF29CE484222325ULL, h1 = h0, h2 = h0;
        for (const auto& e : ev) {
            ladder.apply(e);
            tree.apply(e);
            vec.apply(e);
            h0 = firm::book::l2_hash(ladder, h0);
            h1 = firm::book::l2_hash(tree, h1);
            h2 = firm::book::l2_hash(vec, h2);
        }
        std::printf("%s: ladder %016llx tree %016llx vector %016llx\n", name.c_str(), static_cast<unsigned long long>(h0),
                    static_cast<unsigned long long>(h1), static_cast<unsigned long long>(h2));
        if (h0 != h1 || h0 != h2) ++fails;
    }
    return fails;
}
