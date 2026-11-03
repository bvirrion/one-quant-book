#include <cstdio>
#include <vector>

struct Instrument {
    virtual ~Instrument() = default;
    virtual double value() const { return 0.0; }
};

struct Bond : Instrument {
    double price;
    explicit Bond(double p) : price(p) {}
    double value() const override { return price; }
};

int main() {
    std::vector<Instrument> book;
    book.push_back(Bond(99.5));
    Bond b(101.0);
    Instrument& ref = b;
    Instrument copy = b;
    std::printf("%.1f %.1f %.1f\n", book[0].value(), ref.value(), copy.value());
}
