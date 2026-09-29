import math

ticks = [0.1] * 10
print(sum(ticks) == 1.0, sum(ticks))
print(math.fsum(ticks) == 1.0)
