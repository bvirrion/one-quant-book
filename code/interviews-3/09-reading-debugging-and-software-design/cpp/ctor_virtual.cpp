#include <cstdio>

struct Strategy {
    Strategy() { std::printf("start %s\n", name()); }
    virtual ~Strategy() = default;
    virtual const char* name() const { return "base"; }
};

struct Momentum : Strategy {
    const char* name() const override { return "momentum"; }
};

int main() {
    Momentum m;
    std::printf("run %s\n", m.name());
}
