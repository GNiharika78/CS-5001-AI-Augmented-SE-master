import math

def sumofFactors(n):
    if n % 2 != 0:
        return 0
    result = 1
    for factor in range(2, int(math.sqrt(n)) + 1):
        count = 0
        current_sum = 1
        current_term = 1
        while n % factor == 0:
            count += 1
            n = n // factor
            if factor == 2 and count == 1:
                current_sum = 0
            current_term *= factor
            current_sum += current_term
        result *= current_sum
    if n >= 2:
        result *= (1 + n)
    return result
