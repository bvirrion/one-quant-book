#include <iostream>
#include <memory>
#include <vector>

template <class Derived>
struct Strat {
    long on_tick(long px) { return static_cast<Derived*>(this)->signal(px) * 2; }
};
struct Momo : Strat<Momo> {
    long signal(long px) { return px + 1; }
};

struct IStrat {
    virtual long signal(long px) = 0;
    virtual ~IStrat() = default;
};
struct A : IStrat { long signal(long px) override { return px + 1; } };
struct B : IStrat { long signal(long px) override { return px - 1; } };

long static_call(Momo& s, long px) { return s.on_tick(px); }
long virtual_call(IStrat& s, long px) { return s.signal(px) * 2; }

int main() {
    Momo m;
    std::vector<std::unique_ptr<IStrat>> all;
    all.push_back(std::make_unique<A>());
    all.push_back(std::make_unique<B>());
    long sum = static_call(m, 10);
    for (auto& s : all) sum += virtual_call(*s, 10);
    std::cout << sum << "\n";
}
