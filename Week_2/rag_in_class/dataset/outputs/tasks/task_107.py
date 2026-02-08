def count_Hexadecimal(L, R):
    count = 0
    for num in range(L, R + 1):
        if 10 <= num <= 15:
            count += 1
        elif num > 15:
            current = num
            while current != 0:
                if current % 16 >= 10:
                    count += 1
                current = current // 16
    return count
