def digit_distance_nums(n1, n2):
    difference = abs(n1 - n2)
    return sum(int(digit) for digit in str(difference))
