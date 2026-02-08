# Model output for task_107

## Model
- devstral-small-2:24b-cloud

## Original Code:

def count_Hexadecimal(L,R) :  
    count = 0;  
    for i in range(L,R + 1) : 
        if (i >= 10 and i <= 15) : 
            count += 1;  
        elif (i > 15) : 
            k = i;  
            while (k != 0) :  
                if (k % 16 >= 10) : 
                    count += 1;  
                k = k // 16;  
    return count;  

## Refactored Code:

```python
def count_Hexadecimal(L, R):
    count = 0
    for num in range(L, R + 1):
        if 10 <= num <= 15:
            count += 1
        elif num > 15:
            current = num
            while current != 0:
                if current % 16 >= 10:
                    count += 1
                current = current // 16
    return count
```

- Preserved the exact function name `count_Hexadecimal` and its parameters `(L, R)`
- Maintained the same return type and logic for counting hexadecimal digits
- Kept the same control flow structure (if-elif while)
- Used only standard library operations
- No side effects added
- Improved readability through better variable naming and spacing while keeping identical behavior
- Preserved all edge cases and quirks from the original implementation
- No new dependencies or imports added
- Function remains at module scope as required
