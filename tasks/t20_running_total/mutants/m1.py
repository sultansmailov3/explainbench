def running_total(xs):
    out = []
    t = 1
    for x in xs:
        t += x
        out.append(t)
    return out
