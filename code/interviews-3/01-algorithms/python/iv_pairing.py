def max_pairs(buyers, compatible):
    """compatible[b]: the sellers buyer b may trade with. Each order trades at most once."""
    partner = {}                      # seller -> buyer

    def try_buyer(b, seen):           # find b a seller, moving other buyers if need be
        for s in compatible[b]:
            if s not in seen:
                seen.add(s)
                if s not in partner or try_buyer(partner[s], seen):
                    partner[s] = b
                    return True
        return False

    return sum(try_buyer(b, set()) for b in buyers), partner


# Not printed: the same search with an explicit stack, for an augmenting path longer than the recursion limit.
def max_pairs_stack(buyers, compatible):
    partner, seller_of, pairs = {}, {}, 0
    for start in buyers:
        via, stack, free = {}, [start], None         # via: seller -> the buyer that reached it
        while stack and free is None:
            b = stack.pop()
            for s in compatible[b]:
                if s not in via:
                    via[s] = b
                    if s not in partner:
                        free = s
                        break
                    stack.append(partner[s])
        if free is not None:
            pairs += 1
        while free is not None:                      # flip the path, back to the start
            b = via[free]
            previous = seller_of.get(b)
            partner[free], seller_of[b] = b, free
            free = previous
    return pairs, partner
