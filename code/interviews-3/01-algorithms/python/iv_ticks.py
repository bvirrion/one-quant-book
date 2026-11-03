def to_ticks(s):
    """The text s, in integer hundredths. ValueError beyond 2 decimals."""
    negative = s.startswith("-")
    whole, _, frac = (s[1:] if negative else s).partition(".")
    if len(frac) > 2 or not (whole + frac).isdigit():
        raise ValueError(s)
    ticks = int(whole or "0") * 100 + int(frac.ljust(2, "0"))
    return -ticks if negative else ticks
