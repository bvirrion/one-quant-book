#include <cstdio>
#include <mutex>
#include <thread>

struct Account { std::mutex m; long balance = 1000; };

void transfer(Account& from, Account& to, long n) {
    std::lock_guard a(from.m);
    std::lock_guard b(to.m);
    from.balance -= n;
    to.balance += n;
}

int main() {
    Account x, y;
    std::thread t1([&] { transfer(x, y, 1); });
    t1.join();
    std::thread t2([&] { transfer(y, x, 1); });
    t2.join();
    std::printf("%ld %ld\n", x.balance, y.balance);
}
