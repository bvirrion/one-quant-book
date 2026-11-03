from functools import wraps


def memo(f):
    cache = {}

    @wraps(f)
    def inner(*args, **kwargs):
        key = (args, tuple(sorted(kwargs.items())))
        if key not in cache:
            cache[key] = f(*args, **kwargs)
        return cache[key]

    return inner
