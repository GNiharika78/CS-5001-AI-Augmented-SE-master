def binary_to_integer(test_tup):
    binary_str = "".join(str(bit) for bit in test_tup)
    decimal_value = int(binary_str, 2)
    return str(decimal_value)
