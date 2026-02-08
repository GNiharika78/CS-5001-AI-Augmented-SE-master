def first_non_repeating_character(input_string):
    character_order = []
    character_counts = {}
    for char in input_string:
        if char in character_counts:
            character_counts[char] += 1
        else:
            character_counts[char] = 1
            character_order.append(char)
    for char in character_order:
        if character_counts[char] == 1:
            return char
    return None
