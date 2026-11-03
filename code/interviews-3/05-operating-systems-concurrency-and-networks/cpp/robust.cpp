#include <cerrno>
#include <cstdio>
#include <ctime>
#include <pthread.h>
#include <sys/mman.h>
#include <sys/wait.h>
#include <unistd.h>

int main(int argc, char**) {
    bool robust = argc == 1;
    void* mem = mmap(nullptr, sizeof(pthread_mutex_t), PROT_READ | PROT_WRITE,
                     MAP_SHARED | MAP_ANONYMOUS, -1, 0);
    auto* m = static_cast<pthread_mutex_t*>(mem);
    pthread_mutexattr_t a;
    pthread_mutexattr_init(&a);
    pthread_mutexattr_setpshared(&a, PTHREAD_PROCESS_SHARED);
    if (robust) pthread_mutexattr_setrobust(&a, PTHREAD_MUTEX_ROBUST);
    pthread_mutex_init(m, &a);
    pid_t pid = fork();
    if (pid == 0) {
        pthread_mutex_lock(m);
        _exit(1);                                // dies holding the lock
    }
    waitpid(pid, nullptr, 0);
    timespec limit;
    clock_gettime(CLOCK_REALTIME, &limit);
    limit.tv_nsec = 0;
    limit.tv_sec += 2;
    int first = pthread_mutex_timedlock(m, &limit);
    const char* name = first == EOWNERDEAD  ? "EOWNERDEAD"
                       : first == ETIMEDOUT ? "ETIMEDOUT"
                                            : "other";
    std::printf("%s\n", name);
    if (first == EOWNERDEAD) {
        pthread_mutex_consistent(m);             // the shared data has been checked
        pthread_mutex_unlock(m);
        std::printf("%d\n", pthread_mutex_lock(m));
    }
}
