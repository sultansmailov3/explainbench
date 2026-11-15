def count_items(xs):
    counts = {}
    for x in xs:
        if x in counts:
            counts[x] += 1
        else:
            counts[x] = 0
    return counts
