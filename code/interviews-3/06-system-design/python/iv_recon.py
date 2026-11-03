"""Compare our fills with the venue's copy, both as exec id -> (order, quantity, price)."""


def reconcile(ours, theirs):
    missing = sorted(set(theirs) - set(ours))        # we never saw these: position is wrong
    extra = sorted(set(ours) - set(theirs))
    differ = sorted(k for k in set(ours) & set(theirs) if ours[k] != theirs[k])
    return {"missing": missing, "extra": extra, "differ": differ}
