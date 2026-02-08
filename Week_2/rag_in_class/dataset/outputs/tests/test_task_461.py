from tasks.task_461 import *

def test_mbpp_asserts():
    assert upper_ctr('PYthon') == 1
    assert upper_ctr('BigData') == 1
    assert upper_ctr('program') == 0
