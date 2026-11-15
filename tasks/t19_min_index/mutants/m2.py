def min_index(xs):
    best = 0
    for i in range(1, len(xs) - 1):
        if xs[i] < xs[best]:
            best = i
    return best
