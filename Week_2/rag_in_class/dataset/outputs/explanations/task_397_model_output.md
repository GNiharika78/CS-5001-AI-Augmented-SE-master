# Model output for task_397

## Model
- devstral-small-2:24b-cloud

## Original Code:

def median_numbers(a,b,c):
 if a > b:
    if a < c:
        median = a
    elif b > c:
        median = b
    else:
        median = c
 else:
    if a > c:
        median = a
    elif b < c:
        median = b
    else:
        median = c
 return median

## Refactored Code:

```python
def median_numbers(a, b, c):
    if a > b:
        if a < c:
            return a
        elif b > c:
            return b
        else:
            return c
    else:
        if a > c:
            return a
        elif b < c:
            return b
        else:
            return c
```

- Preserved the exact function signature and return behavior
- Maintained all original control flow logic without changes
- Kept all variable names and comparison operations identical
- Removed only the intermediate `median` variable assignment
- No new dependencies or side effects introduced
- All edge cases and quirks preserved as per original implementation
- Function remains at module scope with no nesting
- No algorithmic changes - only minor structural simplification
- All test cases should pass exactly as before
