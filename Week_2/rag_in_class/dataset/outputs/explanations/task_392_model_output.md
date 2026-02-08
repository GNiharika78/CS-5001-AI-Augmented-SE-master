# Model output for task_392

## Model
- devstral-small-2:24b-cloud

## Original Code:

def get_max_sum (n):
	res = list()
	res.append(0)
	res.append(1)
	i = 2
	while i<n + 1:
		res.append(max(i, (res[int(i / 2)] 
						+ res[int(i / 3)] +
							res[int(i / 4)]
						+ res[int(i / 5)])))
		i = i + 1
	return res[n]

## Refactored Code:

```python
def get_max_sum(n):
    dp = [0, 1]
    for i in range(2, n + 1):
        dp.append(max(i, dp[int(i / 2)] + dp[int(i / 3)] + dp[int(i / 4)] + dp[int(i / 5)]))
    return dp[n]
```

- Preserved the exact function signature `get_max_sum(n)`
- Maintained the same logic and calculation for dynamic programming array
- Kept the same return value type and behavior
- Used only standard library (no new dependencies)
- No side effects (no prints, I/O, or randomness)
- Simplified variable names while preserving semantics
- Maintained the same loop structure and termination condition
- Preserved integer division behavior with `int(i / divisor)`
- Kept the same edge case handling (n=0, n=1) implicitly through initialization
