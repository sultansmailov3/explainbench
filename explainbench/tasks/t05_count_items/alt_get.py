def count_items(xs):
    counts = {}
    for x in xs:
        counts[x] = counts.get(x, 0) + 1
    return counts
