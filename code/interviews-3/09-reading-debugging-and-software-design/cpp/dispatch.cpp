#include <variant>

struct Signal {
    virtual ~Signal() = default;
    virtual long score(long x) const = 0;
};
struct Momentum final : Signal {
    long score(long x) const override { return 2 * x; }
};
struct Carry final : Signal {
    long score(long x) const override { return x + 1; }
};
using Any = std::variant<Momentum, Carry>;

long by_virtual(const Signal& s, long x) { return s.score(x); }
long by_final(const Momentum& s, long x) { return s.score(x); }
long by_variant(const Any& a, long x) {
    return std::visit([x](const auto& s) { return s.score(x); }, a);
}
long by_switch(const Any& a, long x) {
    if (const auto* m = std::get_if<Momentum>(&a)) return m->score(x);
    return std::get<Carry>(a).score(x);
}
template <class S> long by_template(const S& s, long x) { return s.score(x); }
template long by_template<Momentum>(const Momentum&, long);
