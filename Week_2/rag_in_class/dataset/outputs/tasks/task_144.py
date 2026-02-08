def sum_Pairs(arr, n):
    total = 0
    for index in range(n - 1, -1, -1):
        total += index * arr[index] - (n - 1 - index) * arr[index]
    return total
