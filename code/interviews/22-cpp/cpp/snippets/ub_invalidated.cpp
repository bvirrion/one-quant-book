#include <cstdio>
#include <vector>

int main() {
    std::vector<int> fills;
    fills.push_back(1);
    int& first = fills.front();
    for (int i = 0; i < 100; ++i) fills.push_back(i);  // reallocates: `first` dangles
    std::printf("%d\n", first);
}
