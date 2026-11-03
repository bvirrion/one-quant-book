#pragma GCC diagnostic ignored "-Wreorder"
#include <iostream>

struct Noisy {
    const char* name;
    explicit Noisy(const char* n) : name(n) { std::cout << "+" << name << " "; }
    ~Noisy() { std::cout << "-" << name << " "; }
};

struct Pair {
    Noisy a;
    Noisy b;
    Pair() : b("b"), a("a") {}
};

int main() {
    Pair p;
    std::cout << "body ";
}
