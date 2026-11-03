int read_bad(int* p) {
    int v = *p;
    if (!p) return -1;
    return v;
}

int read_good(int* p) {
    if (!p) return -1;
    return *p;
}
