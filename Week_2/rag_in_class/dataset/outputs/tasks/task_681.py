def smallest_Divisor(n):
    if n % 2 == 0:
        return 2
    divisor = 3
    while divisor * divisor <= n:
        if n % divisor == 0:
            return divisor
        divisor += 2
    return n
