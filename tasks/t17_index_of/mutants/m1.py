def index_of(xs, target):
    for i in range(len(xs) - 1):
        if xs[i] == target:
            return i
    return -1
