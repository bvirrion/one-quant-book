struct S { int x = 1; };
class C { int x = 1; public: int get() const { return x; } };
struct FromC : C {};
class FromS : S {};

int main() {
    // try each line here
}
