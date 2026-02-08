from tasks.task_525 import *

def test_mbpp_asserts():
    assert parallel_lines([2,3,4], [2,3,8]) == True
    assert parallel_lines([2,3,4], [4,-3,8]) == False
    assert parallel_lines([3,3],[5,5]) == True
