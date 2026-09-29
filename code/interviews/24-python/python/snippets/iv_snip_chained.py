import warnings

import pandas as pd

with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    df = pd.DataFrame({"qty": [5, -3, 2], "flag": [0, 0, 0]})
    df[df["qty"] < 0]["flag"] = 1
    print(df["flag"].tolist())
    print(any("SettingWithCopy" in type(w.message).__name__ for w in caught))
df.loc[df["qty"] < 0, "flag"] = 1
print(df["flag"].tolist())
