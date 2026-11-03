#include <cerrno>
#include <cstring>
#include <iostream>
#include <sys/socket.h>
#include <unistd.h>

int main(int argc, char**) {
    int fds[2];
    socketpair(AF_UNIX, SOCK_STREAM, 0, fds);
    close(fds[1]);
    int flags = argc > 1 ? MSG_NOSIGNAL : 0;
    ssize_t n = send(fds[0], "x", 1, flags);
    std::cout << n << " " << std::strerror(errno) << "\n";
}
