import numpy as np

prices = np.array([100.0, 101.0, 102.0, 103.0])
window = prices[1:3]
window[0] = 0.0
picked = prices[[2, 3]]
picked[0] = 0.0
print(prices)
print(np.shares_memory(prices, window), np.shares_memory(prices, picked))
