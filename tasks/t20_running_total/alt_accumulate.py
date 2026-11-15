from itertools import accumulate

def running_total(xs):
    return list(accumulate(xs))
