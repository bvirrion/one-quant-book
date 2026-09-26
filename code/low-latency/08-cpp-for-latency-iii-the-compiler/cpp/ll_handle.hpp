// Chapter 8 of One Quant Book 13: the per-message work of the flag benchmark, declared here, defined in another
// translation unit (ll_handle.cpp), so that only link-time optimisation can inline it into the decode loop.
#pragma once
#include <cstdint>

#include "../../../firm/feed/cpp/firm_feed.hpp"

namespace ll::flags {
struct Stats { std::uint64_t msgs = 0, adds = 0, shares = 0, notional = 0, hash = 1469598103934665603ull; };
void handle(const firm::feed::Msg& m, Stats& s);
}  // namespace ll::flags
