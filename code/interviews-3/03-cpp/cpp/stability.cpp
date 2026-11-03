#include <iostream>
#include <map>
#include <unordered_map>
#include <vector>

int main() {
    std::unordered_map<int, int> u;
    u[1] = 1;
    int* pu = &u[1];
    auto buckets = u.bucket_count();
    for (int i = 2; i < 1000; ++i) u[i] = i;
    std::cout << (u.bucket_count() != buckets) << " " << (pu == &u[1]) << "\n";

    std::map<int, int> m;
    m[1] = 1;
    int* pm = &m[1];
    for (int i = 2; i < 1000; ++i) m[i] = i;
    std::cout << (pm == &m[1]) << "\n";

    std::vector<int> v(1);
    int* pv = &v[0];
    for (int i = 2; i < 1000; ++i) v.push_back(i);
    std::cout << (pv == &v[0]) << "\n";
}
