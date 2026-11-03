#include <iostream>

int main() {
    int a = 1, b = 2;
    int& r = a;
    r = b;
    b = 3;
    std::cout << a << " " << b << " " << r << "\n";
    int* p = &a;
    p = &b;
    *p = 4;
    std::cout << a << " " << b << " " << *p << "\n";
}
