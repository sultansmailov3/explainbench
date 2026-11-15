def first_zero_index(xs):
    for i, x in enumerate(xs):
        if x == 0:
            return i
    return -1
