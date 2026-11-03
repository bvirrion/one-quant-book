#include <iostream>
#include <string>

struct Holder { std::string name; };

std::string make() { return std::string(40, 'x'); }
const std::string& same(const std::string& s) { return s; }

int main() {
    const std::string& one = make();
    const std::string& two = Holder{make()}.name;
    std::cout << one.size() << " " << two.size() << "\n";
    const std::string& three = same(make());
    std::cout << three.size() << "\n";
}
