#include <iostream>

void f(int) { std::cout << "int\n"; }
void f(char*) { std::cout << "pointer\n"; }

template <class T>
void relay(T x) { f(x); }

int main() {
    f(0);
    f(nullptr);
    char* p = nullptr;
    f(p);
    relay(nullptr);
    relay(0);
}
