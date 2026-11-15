def group_by_first_letter(words):
    d = {}
    for w in words:
        if w[0] not in d:
            d[w[0]] = []
        d[w[0]].append(w)
    return d
