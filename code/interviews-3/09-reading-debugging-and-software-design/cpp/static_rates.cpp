#include <cstdlib>

long compute_base() {
    const char* s = std::getenv("BASE_RATE");
    return s ? std::atol(s) : 100;
}

long base_rate = compute_base();
