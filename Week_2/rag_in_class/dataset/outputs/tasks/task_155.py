def even_bit_toggle_number(n):
    result = 0
    bit_position = 0
    temp = n
    while temp > 0:
        if bit_position % 2 == 1:
            result |= 1 << bit_position
        bit_position += 1
        temp >>= 1
    return n ^ result
