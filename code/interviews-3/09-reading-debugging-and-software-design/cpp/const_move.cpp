#include <cstdio>
#include <string>
#include <utility>

struct Tracked {
    inline static int copies = 0, moves = 0;
    std::string text;
    explicit Tracked(std::string t) : text(std::move(t)) {}
    Tracked(const Tracked& o) : text(o.text) { ++copies; }
    Tracked(Tracked&& o) noexcept : text(std::move(o.text)) { ++moves; }
};

class Holder {
public:
    explicit Holder(const Tracked item) : item_(std::move(item)) {}

private:
    Tracked item_;
};

int main() {
    Tracked t("abc");
    Holder h(std::move(t));
    std::printf("copies %d, moves %d\n", Tracked::copies, Tracked::moves);
}
