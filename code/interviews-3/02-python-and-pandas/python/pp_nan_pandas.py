import numpy as np
import pandas as pd

s = pd.Series([1.0, np.nan, 3.0])
print(s.sum(), s.mean(), s.count(), len(s), round(s.fillna(0).mean(), 2))
print(pd.Series([np.nan]).sum(), pd.Series([np.nan]).sum(min_count=1))
print(pd.DataFrame({"k": ["A", None, "A"], "v": [1, 2, 3]}).groupby("k").v.sum().to_dict())
print((s == np.nan).any())
