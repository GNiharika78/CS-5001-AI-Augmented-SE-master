def filter_oddnumbers(nums):
    """Return a list of odd numbers from the input list."""
    odd_nums = [num for num in nums if num % 2 != 0]
    return odd_nums
