def upper_ctr(s):
    count = 0
    for i in range(len(s)):
        if s[i] >= 'A' and s[i] <= 'Z':
            count += 1
        return count
