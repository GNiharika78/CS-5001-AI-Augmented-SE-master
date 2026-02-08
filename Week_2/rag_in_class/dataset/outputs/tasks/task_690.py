def mul_consecutive_nums(nums):
    """Multiply each pair of consecutive numbers in the input list.

    Args:
        nums: List of numbers (int or float)

    Returns:
        List of products of consecutive pairs. For a list of length n,
        returns a list of length n-1.
    """
    if len(nums) < 2:
        return []

    result = []
    for i in range(len(nums) - 1):
        result.append(nums[i] * nums[i + 1])
    return result
