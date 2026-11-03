#include <iostream>
#include <thread>
#include <vector>

template <class V>
void set_both() {
    V flags(2);
    std::thread a([&] { for (int i = 0; i < 2000; ++i) flags[0] = i % 2; });
    std::thread b([&] { for (int i = 0; i < 2000; ++i) flags[1] = i % 2; });
    a.join();
    b.join();
}

int main(int argc, char**) {
    if (argc > 1) set_both<std::vector<bool>>();
    else set_both<std::vector<char>>();
    std::cout << "done\n";
}
