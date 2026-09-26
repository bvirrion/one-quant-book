// Chapter 8: the per-message work, alone in its translation unit.
#include "ll_handle.hpp"

namespace ll::flags {
void handle(const firm::feed::Msg& m, Stats& s) {
    ++s.msgs;
    if (m.kind == 'A') { ++s.adds; s.notional += static_cast<std::uint64_t>(m.price) * m.shares; }
    if (m.kind == 'E') s.shares += m.shares;
    s.hash = (s.hash ^ m.ref) * 1099511628211ull;  // FNV-1a over the order references: the result checksum
}
}  // namespace ll::flags
