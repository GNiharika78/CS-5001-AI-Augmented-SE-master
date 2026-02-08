def frequency_Of_Largest(n, arr):
    max_val = arr[0]
    count = 1
    for i in range(1, n):
        if arr[i] > max_val:
            max_val = arr[i]
            count = 1
        elif arr[i] == max_val:
            count += 1
    return count
