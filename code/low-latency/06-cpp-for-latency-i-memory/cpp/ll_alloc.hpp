// Chapter 6 of One Quant Book 13: where a message handler allocates, and the same handler without allocating.
#pragma once
#include <cstdint>
#include <functional>
#include <map>
#include <string>
#include <string_view>
#include <vector>

#include "../../../firm/arena/cpp/firm_arena.hpp"

namespace ll::alloc {

// Field order as a first draft writes it, and the same fields ordered by size.
struct OrderLoose { char side; double price; char flag; std::uint64_t id; std::uint32_t qty; char tif; };
struct OrderTight { std::uint64_t id; double price; std::uint32_t qty; char side; char flag; char tif; };
static_assert(sizeof(OrderLoose) == 40 && sizeof(OrderTight) == 24);

struct Fill { std::int64_t price; std::uint32_t qty; };

// The naive handler: strings for identifiers, a growing vector of fills, a map from id to state, a callback.
struct NaiveHandler {
    std::map<std::string, int> state;
    std::function<void(const std::vector<Fill>&)> on_done;
    void handle(std::string_view symbol, std::string_view client_id, const Fill* fills, int n) {
        std::string sym(symbol);           // short: fits the string's inline buffer
        std::string cid(client_id);        // 22 characters: one allocation
        std::vector<Fill> fs;              // grows 1, 2, 4: three allocations for three fills
        for (int i = 0; i < n; ++i) fs.push_back(fills[i]);
        state[cid] += n;                   // a new key: one tree node, and a copy of the long key: two
        auto report = [fs, sym](const std::vector<Fill>&) { return fs.size() + sym.size(); };  // copies fs: one
        on_done = report;                  // the function stores a copy of the lambda on the heap: two more
        on_done(fs);
    }
};

// The same work with storage decided in advance.
struct FixedHandler {
    struct Entry { firm::arena::FixedString<24> cid; int fills = 0; };
    firm::arena::FixedVector<Entry, 64> state;
    std::size_t last = 0;
    void handle(std::string_view symbol, std::string_view client_id, const Fill* fills, int n) {
        firm::arena::FixedString<8> sym(symbol);
        firm::arena::FixedString<24> cid(client_id);
        firm::arena::FixedVector<Fill, 8> fs;
        for (int i = 0; i < n; ++i) fs.push_back(fills[i]);
        Entry* e = nullptr;
        for (auto& x : state) if (x.cid == cid) e = &x;
        if (!e && state.push_back(Entry{cid, 0})) e = &state[state.size() - 1];
        if (e) e->fills += n;
        last = fs.size() + sym.view().size();  // the callback's work, done directly
    }
};

}  // namespace ll::alloc
