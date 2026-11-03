import pandas as pd

df = pd.DataFrame({"qty": [1, 2, 3], "px": [4, 5, 6]})
lines = {
    "A": lambda: df[(df.qty > 1) and (df.px < 6)],
    "B": lambda: df[df.qty > 1 & df.px < 6],
    "C": lambda: df[(df.qty > 1) & (df.px < 6)],
}
for name, line in lines.items():
    try:
        print(name, list(line().qty))
    except ValueError:
        print(name, "ValueError")
