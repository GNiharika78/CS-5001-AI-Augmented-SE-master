from tasks.task_101 import *

def test_mbpp_asserts():
    assert kth_element([12,3,5,7,19], 5, 2) == 3
    assert kth_element([17,24,8,23], 4, 3) == 8
    assert kth_element([16,21,25,36,4], 5, 4) == 36
