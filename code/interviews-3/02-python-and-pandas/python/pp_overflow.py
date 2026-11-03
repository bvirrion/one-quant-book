import numpy as np

a = np.array([2**31 - 1], dtype=np.int32)
print(a + 1)
b = np.array([1], dtype=np.uint8)
print(b - 2)
print(2**31 - 1 + 1)
