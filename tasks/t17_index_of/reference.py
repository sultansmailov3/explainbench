def index_of(xs, target):
    for i in range(len(xs)):
        if xs[i] == target:
            return i
    return -1
