#include <iostream>

struct Noisy {
    const char* name;
    explicit Noisy(const char* n) : name(n) { std::cout << "+" << name << " "; }
    ~Noisy() { std::cout << "-" << name << " "; }
};

Noisy global("global");

void f() {
    static Noisy s("static");
    Noisy a("auto");
}

int main() {
    f();
    f();
    Noisy* h = new Noisy("heap");
    (void)h;
    std::cout << "end ";
}
