def unique_items(xs):
    seen = set()
    out = []
    for x in xs:
        if x not in seen:
            out.append(x)
    return out
