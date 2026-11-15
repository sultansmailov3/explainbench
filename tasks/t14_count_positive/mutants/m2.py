def count_positive(xs):
    n = 0
    for x in xs[:-1]:
        if x > 0:
            n += 1
    return n
