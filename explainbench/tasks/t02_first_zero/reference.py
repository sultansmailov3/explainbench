def first_zero_index(xs):
    i = 0
    while i < len(xs):
        if xs[i] == 0:
            return i
        i += 1
    return -1
