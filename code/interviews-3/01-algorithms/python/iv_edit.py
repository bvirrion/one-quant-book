def edit_distance(a, b):
    if len(a) < len(b):
        a, b = b, a                   # keep the shorter one as the row
    row = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        diag, row[0] = row[0], i
        for j, y in enumerate(b, 1):
            cost = diag + (x != y)    # substitute, or keep
            diag = row[j]
            row[j] = min(cost, row[j] + 1, row[j - 1] + 1)
    return row[-1]
