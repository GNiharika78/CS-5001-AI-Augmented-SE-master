def common_element(list1, list2):
    for x in list1:
        for y in list2:
            if x == y:
                return True
    return False
