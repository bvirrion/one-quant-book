import pandas as pd

a = pd.Series([1, 2, 3], index=[1, 2, 3])
b = pd.Series([10, 20, 30], index=[2, 3, 4])
print((a + b).tolist())
print((a.values + b.values).tolist())
print(a.add(b, fill_value=0).tolist())
