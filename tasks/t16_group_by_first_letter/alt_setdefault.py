def group_by_first_letter(words):
    d = {}
    for w in words:
        d.setdefault(w[0], []).append(w)
    return d
