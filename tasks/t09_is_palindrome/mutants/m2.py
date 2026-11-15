def is_palindrome(s):
    i = 0
    j = len(s)
    while i < j:
        if s[i] != s[j]:
            return False
        i += 1
        j -= 1
    return True
