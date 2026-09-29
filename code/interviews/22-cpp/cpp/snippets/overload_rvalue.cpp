#include <cstdio>
#include <string>
#include <utility>

void f(const std::string&) { std::printf("lvalue\n"); }
void f(std::string&&) { std::printf("rvalue\n"); }

void g(std::string&& s) { f(s); }

int main() {
    std::string a = "x";
    f(a);
    f(std::move(a));
    f(std::string("y"));
    g(std::string("z"));
}
