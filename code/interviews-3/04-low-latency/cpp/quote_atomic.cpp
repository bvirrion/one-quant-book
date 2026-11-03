#include <atomic>
#include <cstdio>

struct Small { float bid, ask; };
struct Quote { double bid, ask; };
struct Book { double bid, ask, bid_size; };

std::atomic<Small> small_q;
std::atomic<Quote> quote;
std::atomic<Book> book;

int main() {
    using std::atomic;
    std::printf("%d %d\n", atomic<Small>::is_always_lock_free, small_q.is_lock_free());
    std::printf("%d %d\n", atomic<Quote>::is_always_lock_free, quote.is_lock_free());
    std::printf("%d %d\n", atomic<Book>::is_always_lock_free, book.is_lock_free());
    quote.store(Quote{99.5, 100.5});
    Quote q = quote.load();
    std::printf("%.1f %.1f\n", q.bid, q.ask);
}
