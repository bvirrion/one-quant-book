#include "shm_ring.hpp"
#include <csignal>
#include <cstdio>
#include <new>
#include <sys/mman.h>
#include <sys/wait.h>
#include <unistd.h>

using Ring = ShmRing<1024>;

int main() {
    void* mem = mmap(nullptr, sizeof(Ring), PROT_READ | PROT_WRITE, MAP_SHARED | MAP_ANONYMOUS, -1, 0);
    Ring* ring = ::new (mem) Ring;
    pid_t pid = fork();
    if (pid == 0) {                              // the producer runs until it is killed
        for (std::uint64_t i = 0;; ++i)
            while (!ring->push(i)) {}
    }
    std::uint64_t expected = 0, v;
    long bad = 0;
    while (expected < 200000)                    // the consumer reads a while
        if (ring->pop(v)) bad += v != expected++;
    kill(pid, SIGKILL);
    int status;
    waitpid(pid, &status, 0);
    while (ring->pop(v)) bad += v != expected++;  // whatever was published is whole
    std::printf("%ld %d %d\n", bad, WTERMSIG(status), expected >= 200000);
}
