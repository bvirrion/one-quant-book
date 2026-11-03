#include <cstdio>
#include <functional>
#include <iterator>
#include <list>
#include <memory>
#include <utility>

class Feed {
public:
    using Slot = std::list<std::function<void(long)>>::iterator;
    Slot subscribe(std::function<void(long)> f) {
        subs_.push_back(std::move(f));
        return std::prev(subs_.end());
    }
    void unsubscribe(Slot s) { subs_.erase(s); }
    void publish(long v) { for (auto& f : subs_) f(v); }

private:
    std::list<std::function<void(long)>> subs_;
};

class Strategy {
public:
    explicit Strategy(Feed& feed)
        : feed_(feed), slot_(feed.subscribe([this](long v) { total_ += v; })) {}
    ~Strategy() { feed_.unsubscribe(slot_); }
    Strategy(const Strategy&) = delete;             // [this] is inside the feed: never copy
    Strategy& operator=(const Strategy&) = delete;
    long total() const { return total_; }

private:
    Feed& feed_;
    Feed::Slot slot_;
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
