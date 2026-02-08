import cmath

def angle_complex(a, b):
    complex_number = complex(a, b)
    angle = cmath.phase(a + b)
    return angle
