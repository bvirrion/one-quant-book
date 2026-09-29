#include <cstdio>

int trace(const char* name, int v) {
    std::printf("init %s\n", name);
    return v;
}

int b = trace("b", 2);
int a = trace("a", b + 1);

int main() { std::printf("a=%d b=%d\n", a, b); }
