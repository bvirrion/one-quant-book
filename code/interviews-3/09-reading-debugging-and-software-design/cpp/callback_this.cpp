#include <cstdio>
#include <functional>
#include <memory>
#include <utility>
#include <vector>

class Feed {
public:
    void subscribe(std::function<void(long)> f) { subs_.push_back(std::move(f)); }
    void publish(long v) { for (auto& f : subs_) f(v); }

private:
    std::vector<std::function<void(long)>> subs_;
};

class Strategy {
public:
    explicit Strategy(Feed& feed) { feed.subscribe([this](long v) { total_ += v; }); }
    long total() const { return total_; }

private:
    long total_ = 0;
};

int main() {
    Feed feed;
    auto s = std::make_unique<Strategy>(feed);
    feed.publish(1);
    std::printf("%ld\n", s->total());
    s.reset();
    feed.publish(2);
    std::puts("done");
}
