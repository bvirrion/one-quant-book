import numpy as np

a = np.arange(5)
b = a[1:3]
b[0] = 99
c = a[[3, 4]]
c[0] = 77
d = a[a > 3]
d[0] = 55
print(a)
