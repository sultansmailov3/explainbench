def group_by_first_letter(words):
    d = {}
    for w in words:
        d[w[0]] = [w]
    return d
