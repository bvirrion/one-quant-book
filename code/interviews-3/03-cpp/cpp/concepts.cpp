#include <concepts>
#include <iostream>
#include <type_traits>

template <std::integral T>
const char* kind(T) { return "integer"; }

template <std::floating_point T>
const char* kind(T) { return "real"; }

template <class T>
concept Priced = requires(const T& t) {
    { t.price() } -> std::convertible_to<double>;
};

template <Priced T>
double notional(const T& t, int qty) { return t.price() * qty; }

struct Fill { double price() const { return 2.5; } };

int main() {
    std::cout << kind(1) << " " << kind(1.0) << " " << kind(1L) << "\n";
    std::cout << notional(Fill{}, 4) << "\n";
    // try each line here
}
