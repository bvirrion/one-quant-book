#include <atomic>
#include <cstdio>
#include <filesystem>
#include <mutex>
#include <sys/wait.h>
#include <thread>
#include <unistd.h>

std::mutex m;

static long threads() {
    long n = 0;
    for (auto& e : std::filesystem::directory_iterator("/proc/self/task"))
        n += !e.path().empty();
    return n;
}

int main() {
    std::atomic<bool> held{false}, done{false};
    std::thread t([&] {
        std::lock_guard g(m);
        held = true;
        while (!done) std::this_thread::yield();
    });
    while (!held) std::this_thread::yield();
    std::printf("parent threads %ld\n", threads());
    std::fflush(stdout);
    pid_t pid = fork();
    if (pid == 0) {
        std::printf("child threads %ld, try_lock %d\n", threads(), m.try_lock());
        std::fflush(stdout);
        _exit(0);
    }
    waitpid(pid, nullptr, 0);
    done = true;
    t.join();
    std::printf("parent try_lock %d\n", m.try_lock());
}
