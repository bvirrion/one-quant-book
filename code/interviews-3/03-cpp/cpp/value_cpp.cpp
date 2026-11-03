#include <iostream>
#include <vector>

struct Fill { int qty; };

int main() {
    Fill a{1};
    Fill copy = a;
    a.qty = 2;
    std::vector<Fill> list{a};
    list[0].qty = 9;
    Fill& ref = a;
    ref.qty = 3;
    std::cout << a.qty << " " << copy.qty << " " << list[0].qty << "\n";
}
