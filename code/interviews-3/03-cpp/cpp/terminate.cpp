#pragma GCC diagnostic ignored "-Wterminate"
#include <iostream>
#include <stdexcept>
#include <cstring>

void promised() noexcept { throw std::runtime_error("from noexcept"); }

struct Closer {
    ~Closer() { throw std::runtime_error("from destructor"); }
};

int main(int, char** argv) {
    try {
        if (!std::strcmp(argv[1], "noexcept")) promised();
        if (!std::strcmp(argv[1], "destructor")) { Closer c; }
        if (!std::strcmp(argv[1], "plain")) throw std::runtime_error("plain");
    } catch (const std::exception& e) {
        std::cout << "caught " << e.what() << "\n";
    }
}
