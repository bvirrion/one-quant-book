#include <cstdio>
#include <string>
#include <string_view>

std::string symbol() { return std::string("A_VERY_LONG_INSTRUMENT_SYMBOL_THAT_DEFEATS_SSO"); }

int main() {
    std::string_view s = symbol();  // the temporary string is destroyed at the end of this line
    std::printf("%c\n", s[0]);
}
