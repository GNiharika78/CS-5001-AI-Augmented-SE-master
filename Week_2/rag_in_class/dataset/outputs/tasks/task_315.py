def find_Max_Len_Even(s):
    n = len(s)
    i = 0
    current_length = 0
    max_length = 0
    start_index = -1

    while i < n:
        if s[i] == ' ':
            if current_length % 2 == 0:
                if max_length < current_length:
                    max_length = current_length
                    start_index = i - current_length
            current_length = 0
        else:
            current_length += 1
        i += 1

    if current_length % 2 == 0:
        if max_length < current_length:
            max_length = current_length
            start_index = i - current_length

    if start_index == -1:
        return "-1"
    return s[start_index: start_index + max_length]
