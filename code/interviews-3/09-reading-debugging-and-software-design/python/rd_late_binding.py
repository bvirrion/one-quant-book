# ruff: noqa: B023
def make_scalers():
    scalers = []
    for k in [1, 2, 3]:
        scalers.append(lambda x: k * x)
    return scalers


print([f(10) for f in make_scalers()])
