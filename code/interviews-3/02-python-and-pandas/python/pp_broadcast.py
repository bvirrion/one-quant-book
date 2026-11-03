import numpy as np

r = np.array([[1.0, 2.0], [3.0, 6.0]])
print(r - r.mean(axis=1))
print(r - r.mean(axis=1, keepdims=True))
