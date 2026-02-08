# Model output for task_453

## Model
- devstral-small-2:24b-cloud

## Original Code:

import math 
def sumofFactors(n) : 
    if (n % 2 != 0) : 
        return 0
    res = 1
    for i in range(2, (int)(math.sqrt(n)) + 1) :    
        count = 0
        curr_sum = 1
        curr_term = 1
        while (n % i == 0) : 
            count= count + 1
            n = n // i 
            if (i == 2 and count == 1) : 
                curr_sum = 0
            curr_term = curr_term * i 
            curr_sum = curr_sum + curr_term 
        res = res * curr_sum  
    if (n >= 2) : 
        res = res * (1 + n) 
    return res 

## Refactored Code:

```python
import math

def sumofFactors(n):
    if n % 2 != 0:
        return 0
    result = 1
    for factor in range(2, int(math.sqrt(n)) + 1):
        count = 0
        current_sum = 1
        current_term = 1
        while n % factor == 0:
            count += 1
            n = n // factor
            if factor == 2 and count == 1:
                current_sum = 0
            current_term *= factor
            current_sum += current_term
        result *= current_sum
    if n >= 2:
        result *= (1 + n)
    return result
```

- Preserved the exact function signature and public API
- Maintained all original logic and edge cases
- Kept the same mathematical operations and control flow
- Used only standard library imports (math)
- No side effects added
- Improved variable names for readability while keeping behavior identical
- Preserved all quirks (e.g., special handling for factor 2 with count=1)
- No algorithm changes or optimizations that could alter behavior
- All tests should pass exactly as before
