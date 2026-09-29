#include <cstdio>
#include <functional>
#include <memory>

int main() {
    std::printf("%zu %zu %zu\n", sizeof(std::unique_ptr<int>), sizeof(std::shared_ptr<int>),
                sizeof(std::function<void()>));
}
