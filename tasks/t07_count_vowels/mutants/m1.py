def count_vowels(s):
    n = 0
    for ch in s.lower()[1:]:
        if ch in "aeiou":
            n += 1
    return n
