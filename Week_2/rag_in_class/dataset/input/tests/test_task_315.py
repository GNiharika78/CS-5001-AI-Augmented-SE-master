from tasks.task_315 import *

def test_mbpp_asserts():
    assert find_Max_Len_Even("python language") == "language"
    assert find_Max_Len_Even("maximum even length") == "length"
    assert find_Max_Len_Even("eve") == "-1"
