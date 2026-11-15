def reverse_list(xs):
    result = []
    i = len(xs) - 1
    while i > 0:
        result.append(xs[i])
        i -= 1
    return result
