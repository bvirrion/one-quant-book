#include <cstdio>
#include <utility>
#include <vector>

int main() {
    std::vector<int> v{1, 2, 3};
    std::vector<int> w = std::move(v);
    // v is valid but unspecified: only operations without preconditions are safe.
    std::printf("w=%zu v=%zu\n", w.size(), v.size());
    v.assign({7});
    std::printf("v[0]=%d\n", v[0]);
}
