#include <iostream>

struct Base {
    virtual void f(int x = 1) { std::cout << "Base " << x << "\n"; }
    void g(int) { std::cout << "Base::g(int)\n"; }
    virtual ~Base() = default;
};

struct Derived : Base {
    void f(int x = 2) override { std::cout << "Derived " << x << "\n"; }
    void g(double) { std::cout << "Derived::g(double)\n"; }
};

int main() {
    Derived d;
    Base& b = d;
    b.f();
    d.f();
    b.g(1);
    d.g(1);
}
