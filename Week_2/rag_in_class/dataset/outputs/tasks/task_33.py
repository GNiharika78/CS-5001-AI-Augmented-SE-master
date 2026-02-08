def decimal_To_Binary(N):
    binary_number = 0
    position = 0
    while N != 0:
        remainder = N % 2
        binary_number += remainder * (10 ** position)
        N = N // 2
        position += 1
    return binary_number
