#include <cstring>
#include <iostream>
#include <string>
#include <string_view>

int main() {
    std::string_view line = "ESZ6,4501.25";
    std::string_view sym = line.substr(0, 4);
    std::cout << sym.size() << " " << std::strlen(sym.data()) << "\n";
    std::cout << std::strlen(std::string(sym).c_str()) << "\n";
}
