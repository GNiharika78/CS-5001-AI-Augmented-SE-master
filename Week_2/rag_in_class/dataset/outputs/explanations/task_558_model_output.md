# Model output for task_558

## Model
- devstral-small-2:24b-cloud

## Original Code:

def digit_distance_nums(n1, n2):
         return sum(map(int,str(abs(n1-n2))))

## Refactored Code:

```python
def digit_distance_nums(n1, n2):
    difference = abs(n1 - n2)
    return sum(int(digit) for digit in str(difference))
```

- Preserved the exact function name `digit_distance_nums` and its parameters `n1` and `n2`
- Maintained the same return type and behavior (sum of digits of absolute difference)
- Kept the logic of calculating absolute difference and converting to string
- Used a generator expression instead of `map` for better readability while maintaining identical behavior
- No changes to edge cases or special behaviors (e.g., negative numbers, zero)
- No new dependencies or imports added
- No side effects introduced
- Function remains at module scope
- Preserved all original semantics exactly as required
