positions = {"A": 0, "B": 5, "C": 0}
try:
    for sym, qty in positions.items():
        if qty == 0:
            del positions[sym]
except RuntimeError as e:
    print("RuntimeError:", e)
positions = {s: q for s, q in {"A": 0, "B": 5, "C": 0}.items() if q != 0}
print(positions)
