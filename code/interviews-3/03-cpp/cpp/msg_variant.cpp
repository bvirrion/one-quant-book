#include <iostream>
#include <variant>

struct Add { int id; int qty; };
struct Cancel { int id; };
struct Trade { int qty; long px; };
using Msg = std::variant<Add, Cancel, Trade>;

template <class... F>
struct Overload : F... { using F::operator()...; };

long apply(const Msg& m) {
    return std::visit(Overload{
        [](const Add& a) -> long { return a.qty; },
        [](const Cancel&) -> long { return 0; },
        [](const Trade& t) -> long { return t.qty * t.px; },
    }, m);
}

int main() {
    Msg m = Trade{3, 100};
    std::cout << apply(m) << " " << m.index() << " " << sizeof(Msg) << "\n";
    std::cout << (std::get_if<Add>(&m) == nullptr) << "\n";
    try {
        std::get<Add>(m);
    } catch (const std::bad_variant_access&) {
        std::cout << "bad access\n";
    }
    m = Cancel{9};
    std::cout << apply(m) << " " << m.index() << "\n";
}
