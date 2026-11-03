#include <iostream>
#include <new>

int main() {
    alignas(double) char buf[32];
    double* p = ::new (static_cast<void*>(buf + 1)) double(1.5);
    std::cout << *p << "\n";
}
