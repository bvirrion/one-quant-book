#include "bq.hpp"
#include <atomic>
#include <iostream>
#include <thread>
#include <vector>

int main() {
    BoundedQueue<long> q(4);
    std::atomic<long> sum{0}, got{0};
    std::vector<std::thread> ps, cs;
    for (int c = 0; c < 3; ++c)
        cs.emplace_back([&] {
            while (auto x = q.pop()) { sum += *x; ++got; }
        });
    for (int p = 0; p < 3; ++p)
        ps.emplace_back([&, p] {
            for (long i = 1; i <= 3000; ++i) q.push(i * (p + 1));
        });
    for (auto& t : ps) t.join();
    q.close();
    for (auto& t : cs) t.join();
    std::cout << got << " " << sum << " " << q.push(1) << " " << q.pop().has_value() << "\n";
    // a producer blocked on a full queue wakes on close and reports it
    BoundedQueue<int> full(1);
    full.push(1);
    std::atomic<int> result{-1};
    std::thread blocked([&] { result = full.push(2); });
    full.close();
    blocked.join();
    std::cout << result << " " << *full.pop() << " " << full.pop().has_value() << "\n";
}
