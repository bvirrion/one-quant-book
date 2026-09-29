#include <cstdio>

struct Noisy {
    const char* tag;
    explicit Noisy(const char* t) : tag(t) { std::printf("make %s\n", tag); }
    ~Noisy() { std::printf("drop %s\n", tag); }
};

struct Pair {
    Noisy second{"second"};
    Noisy first{"first"};
    Pair() { std::printf("body\n"); }
};

int use(const Noisy& n) { return n.tag[0]; }

int main() {
    Pair p;
    int c = use(Noisy{"temp"});
    std::printf("after %c\n", c);
}
