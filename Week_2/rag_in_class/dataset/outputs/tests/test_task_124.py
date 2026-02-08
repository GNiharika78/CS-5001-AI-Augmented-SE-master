from tasks.task_124 import *

def test_mbpp_asserts():
    assert angle_complex(0,1j)==1.5707963267948966
    assert angle_complex(2,1j)==0.4636476090008061
    assert angle_complex(0,2j)==1.5707963267948966
