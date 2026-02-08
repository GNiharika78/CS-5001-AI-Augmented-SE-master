def parallel_lines(line1, line2):
    slope1 = line1[0] / line1[1]
    slope2 = line2[0] / line2[1]
    return slope1 == slope2
