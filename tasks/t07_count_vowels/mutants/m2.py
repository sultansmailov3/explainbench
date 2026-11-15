def count_vowels(s):
    n = 1
    for ch in s.lower():
        if ch in "aeiou":
            n += 1
    return n
