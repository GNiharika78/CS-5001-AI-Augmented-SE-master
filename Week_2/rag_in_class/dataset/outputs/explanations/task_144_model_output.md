# Model output for task_144

## Model
- devstral-small-2:24b-cloud

## Original Code:

def sum_Pairs(arr,n): 
    sum = 0
    for i in range(n - 1,-1,-1): 
        sum += i*arr[i] - (n-1-i) * arr[i] 
    return sum

## Refactored Code:

```python
def sum_Pairs(arr, n):
    total = 0
    for index in range(n - 1, -1, -1):
        total += index * arr[index] - (n - 1 - index) * arr[index]
    return total
```

- Preserved the exact function name `sum_Pairs` and its parameters `(arr, n)`
- Maintained the same return type and value calculation logic
- Kept the loop structure and iteration direction (backwards from n-1 to 0)
- Used more descriptive variable names (`total` instead of `sum`, `index` instead of `i`)
- Preserved the exact mathematical operation in the loop body
- No changes to the algorithm or logic flow
- No new dependencies or side effects added
- All functions remain at module scope
- Behavior is identical to the original implementation
