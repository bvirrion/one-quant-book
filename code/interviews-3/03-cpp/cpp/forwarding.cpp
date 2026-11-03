#include <iostream>
#include <string>
#include <utility>

void take(const std::string&) { std::cout << "copy\n"; }
void take(std::string&&) { std::cout << "move\n"; }

template <class T>
void bad(T&& x) { take(x); }

template <class T>
void good(T&& x) { take(std::forward<T>(x)); }

int main() {
    std::string s = "abc";
    bad(s);
    bad(std::string("abc"));
    good(s);
    good(std::string("abc"));
    good(std::move(s));
}
