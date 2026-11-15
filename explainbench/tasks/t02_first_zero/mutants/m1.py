def first_zero_index(xs):
    i = 0
    while i < len(xs) - 1:
        if xs[i] == 0:
            return i
        i += 1
    return -1
