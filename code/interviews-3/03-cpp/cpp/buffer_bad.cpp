struct Buffer {
    double* data;
    explicit Buffer(int n) : data(new double[n]{}) {}
    ~Buffer() { delete[] data; }
};

int main() {
    Buffer a(4);
    {
        Buffer b = a;
        b.data[0] = 1.0;
    }
    a.data[0] = 2.0;
}
