from decimal import ROUND_HALF_UP, Decimal

print(round(2.5), round(3.5), round(2.675, 2))
print(Decimal(2.675))
print(Decimal(0.1) == Decimal("0.1"))
print(Decimal("2.675").quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
