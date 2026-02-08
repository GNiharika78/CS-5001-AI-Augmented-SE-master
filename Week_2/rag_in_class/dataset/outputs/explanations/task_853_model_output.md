# Model output for task_853

## Model
- devstral-small-2:24b-cloud

## Original Code:

import math
def sum_of_odd_Factors(n): 
    res = 1
    while n % 2 == 0: 
        n = n // 2 
    for i in range(3,int(math.sqrt(n) + 1)): 
        count = 0
        curr_sum = 1
        curr_term = 1
        while n % i == 0: 
            count+=1 
            n = n // i 
            curr_term *= i 
            curr_sum += curr_term    
        res *= curr_sum  
    if n >= 2: 
        res *= (1 + n) 
    return res 

## Refactored Code:

```python
import math

def sum_of_odd_Factors(n):
    result = 1
    # Remove all factors of 2 (even factors)
    while n % 2 == 0:
        n = n // 2

    # Check odd factors from 3 up to sqrt(n)
    for factor in range(3, int(math.sqrt(n)) + 1):
        current_sum = 1
        current_term = 1
        while n % factor == 0:
            n = n // factor
            current_term *= factor
            current_sum += current_term
        result *= current_sum

    # Handle remaining prime factor >= 2
    if n >= 2:
        result *= (1 + n)

    return result
```

- Preserved the exact function name and signature `sum_of_odd_Factors(n)`
- Maintained all original logic including the factor removal and summation process
- Kept the same mathematical operations and control flow structure
- Used only standard library imports (math)
- No side effects added (no prints, logging, etc.)
- Improved variable names for clarity while keeping the same behavior
- Preserved all edge cases and quirks from the original implementation
- Kept the function at module scope as required
- Maintained the exact same return value behavior for all inputs
