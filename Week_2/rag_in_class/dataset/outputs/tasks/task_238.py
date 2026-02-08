def number_of_substrings(input_str):
    length = len(input_str)
    return int(length * (length + 1) / 2)
