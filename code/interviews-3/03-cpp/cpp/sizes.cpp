#include <functional>
#include <iostream>
#include <memory>
#include <string>
#include <vector>

struct Empty {};
struct Virt { virtual ~Virt() = default; };
struct Base1 : Empty { int x; };
struct Member { Empty e; int x; };
struct Attr { [[no_unique_address]] Empty e; int x; };
void close_it(int* p) { delete p; }

int main() {
    auto lambda = [](int* p) { delete p; };
    std::cout << sizeof(Empty) << " " << sizeof(Virt) << " " << sizeof(Base1) << " "
              << sizeof(Member) << " " << sizeof(Attr) << "\n";
    std::cout << sizeof(std::unique_ptr<int>) << " "
              << sizeof(std::unique_ptr<int, decltype(lambda)>) << " "
              << sizeof(std::unique_ptr<int, void (*)(int*)>) << "\n";
    std::cout << sizeof(std::shared_ptr<int>) << " " << sizeof(std::function<void()>) << " "
              << sizeof(std::string) << " " << sizeof(std::vector<int>) << "\n";
}
