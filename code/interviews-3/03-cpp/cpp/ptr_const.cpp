int main() {
    int a = 1, b = 2;
    const int* p = &a;
    int* const q = &a;
    const int* const r = &a;
    (void)b, (void)p, (void)q, (void)r;
    // try each line here
}
