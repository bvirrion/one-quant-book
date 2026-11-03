#include <iostream>
#include <vector>

int main() {
    std::vector<int> a(3, 1), b{3, 1}, c(3), d{3};
    std::cout << a.size() << " " << b.size() << " " << c.size() << " " << d.size() << "\n";
    std::cout << a[0] << " " << b[0] << " " << c[0] << " " << d[0] << "\n";
}
