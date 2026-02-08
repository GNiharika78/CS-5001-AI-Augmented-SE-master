import math

def area_pentagon(a):
    """Calculate the area of a regular pentagon with side length a."""
    constant = math.sqrt(5 * (5 + 2 * math.sqrt(5))) / 4.0
    return constant * (a ** 2)
