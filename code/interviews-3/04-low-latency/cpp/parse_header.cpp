#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstring>

struct Header {
    std::uint32_t seq;
    std::uint64_t ts;
};

std::uint64_t ts_cast(const unsigned char* p) {
    return reinterpret_cast<const Header*>(p)->ts;
}

std::uint64_t ts_copy(const unsigned char* p) {
    std::uint64_t ts;
    std::memcpy(&ts, p + offsetof(Header, ts), sizeof ts);
    return ts;
}

int main() {
    alignas(8) unsigned char packet[64] = {};
    std::uint64_t stamp = 123456789;
    std::memcpy(packet + 3 + offsetof(Header, ts), &stamp, sizeof stamp);
    std::printf("%llu\n", static_cast<unsigned long long>(ts_cast(packet + 3)));
    std::printf("%llu\n", static_cast<unsigned long long>(ts_copy(packet + 3)));
}
