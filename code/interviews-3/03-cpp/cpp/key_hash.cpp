#include <cstddef>
#include <functional>
#include <iostream>
#include <unordered_map>

struct Key {
    int symbol;
    int venue;
    bool operator==(const Key&) const = default;
};

struct Weak {
    std::size_t operator()(const Key& k) const { return k.symbol; }
};

struct Mixed {
    std::size_t operator()(const Key& k) const {
        std::size_t h = std::hash<long>{}((long(k.symbol) << 32) | unsigned(k.venue));
        return h * 0x9E3779B97F4A7C15ull;
    }
};

template <class H>
std::size_t worst_bucket() {
    std::unordered_map<Key, int, H> m;
    for (int s = 0; s < 100; ++s)
        for (int v = 0; v < 50; ++v) m[Key{s, v}] = v;
    std::size_t worst = 0;
    for (std::size_t b = 0; b < m.bucket_count(); ++b)
        worst = std::max(worst, m.bucket_size(b));
    return worst;
}

int main() {
    std::cout << worst_bucket<Weak>() << " " << worst_bucket<Mixed>() << "\n";
}
