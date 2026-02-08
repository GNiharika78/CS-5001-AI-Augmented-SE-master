# Model output for task_153

## Model
- devstral-small-2:24b-cloud

## Original Code:

def parabola_vertex(a, b, c): 
  vertex=(((-b / (2 * a)),(((4 * a * c) - (b * b)) / (4 * a))))
  return vertex

## Refactored Code:

```python
def parabola_vertex(a, b, c):
    x_vertex = -b / (2 * a)
    y_vertex = (4 * a * c - b * b) / (4 * a)
    return (x_vertex, y_vertex)
```

- Preserved the exact function name, parameters, and return type
- Maintained the original mathematical operations without modification
- Kept the function at module scope
- Used only standard library operations
- No side effects added
- Improved readability by breaking down the calculation into separate steps
- Preserved all edge cases and quirks of the original implementation
- No new dependencies introduced
- Followed conservative refactoring approach
