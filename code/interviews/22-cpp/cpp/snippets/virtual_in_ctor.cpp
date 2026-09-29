#include <cstdio>

struct Base {
    Base() { std::printf("%s\n", name()); }
    virtual ~Base() = default;
    virtual const char* name() const { return "Base"; }
};

struct Derived : Base {
    Derived() { std::printf("%s\n", name()); }
    const char* name() const override { return "Derived"; }
};

int main() {
    Derived d;
    const Base& b = d;
    std::printf("%s\n", b.name());
}
