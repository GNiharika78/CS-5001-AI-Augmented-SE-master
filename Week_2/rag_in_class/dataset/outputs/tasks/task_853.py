import math

def sum_of_odd_Factors(n):
    result = 1
    # Remove all factors of 2 (even factors)
    while n % 2 == 0:
        n = n // 2

    # Check odd factors from 3 up to sqrt(n)
    for factor in range(3, int(math.sqrt(n)) + 1):
        current_sum = 1
        current_term = 1
        while n % factor == 0:
            n = n // factor
            current_term *= factor
            current_sum += current_term
        result *= current_sum

    # Handle remaining prime factor >= 2
    if n >= 2:
        result *= (1 + n)

    return result
