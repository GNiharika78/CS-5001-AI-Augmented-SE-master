from tasks.task_940 import *

def test_task_940():
    assert heap_sort([12, 2, 4, 5, 2, 3]) == [2, 2, 3, 4, 5, 12]
    assert heap_sort([32, 14, 5, 6, 7, 19]) == [5, 6, 7, 14, 19, 32]
    assert heap_sort([21, 15, 29, 78, 65]) == [15, 21, 29, 65, 78]
