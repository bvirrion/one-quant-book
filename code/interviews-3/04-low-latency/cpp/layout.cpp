#include <cstddef>
#include <cstdio>

struct A { char c; double d; char e; int i; };
struct B { double d; int i; char c; char e; };
struct alignas(64) C { int x; };

int main() {
    C row[3];
    std::printf("%zu %zu %zu %zu\n", sizeof(A), sizeof(B), sizeof(C), sizeof(row));
    std::printf("%zu %zu\n", offsetof(A, e), offsetof(B, e));
}
