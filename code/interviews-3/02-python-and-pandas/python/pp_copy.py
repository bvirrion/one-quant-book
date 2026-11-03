import copy

orders = {"A": [1, 2]}
shallow = orders.copy()
deep = copy.deepcopy(orders)
orders["A"].append(3)
orders["B"] = [9]
print(shallow)
print(deep)
