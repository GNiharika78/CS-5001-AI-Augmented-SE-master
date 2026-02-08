from tasks.task_494 import *

def test_task_494():
    assert binary_to_integer((1, 1, 0, 1, 0, 0, 1)) == '105'
    assert binary_to_integer((0, 1, 1, 0, 0, 1, 0, 1)) == '101'
    assert binary_to_integer((1, 1, 0, 1, 0, 1)) == '53'
