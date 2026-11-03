#include <chrono>
#include <condition_variable>
#include <cstdio>
#include <deque>
#include <mutex>
#include <thread>

std::mutex m;
std::condition_variable cv;
std::deque<int> q;

int pop() {
    std::unique_lock lock(m);
    if (q.empty()) cv.wait(lock);
    const int v = q.front();
    q.pop_front();
    return v;
}

void push(int v) {
    {
        std::lock_guard lock(m);
        q.push_back(v);
    }
    cv.notify_all();
}

int main() {
    std::thread a([] { std::printf("a %d\n", pop()); });
    std::thread b([] { std::printf("b %d\n", pop()); });
    std::this_thread::sleep_for(std::chrono::milliseconds(200));
    push(7);
    std::this_thread::sleep_for(std::chrono::milliseconds(200));
    push(8);
    a.join();
    b.join();
}
