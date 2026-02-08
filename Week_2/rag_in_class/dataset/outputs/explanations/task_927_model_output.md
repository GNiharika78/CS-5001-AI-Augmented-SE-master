# Model output for task_927

## Model
- devstral-small-2:24b-cloud

## Original Code:

class Node: 
	def __init__(self, data): 
		self.data = data 
		self.left = None
		self.right = None
def max_height(node): 
	if node is None: 
		return 0 ; 
	else : 
		left_height = max_height(node.left) 
		right_height = max_height(node.right) 
		if (left_height > right_height): 
			return left_height+1
		else: 
			return right_height+1

## Refactored Code:

```python
class Node:
    def __init__(self, data):
        self.data = data
        self.left = None
        self.right = None

def max_height(node):
    if node is None:
        return 0
    left_height = max_height(node.left)
    right_height = max_height(node.right)
    return max(left_height, right_height) + 1
```

- Preserved the public API exactly (Node class and max_height function unchanged)
- Maintained identical semantics (same logic for height calculation)
- Kept functions at module scope (no nesting or wrapping)
- Used only standard library (no new dependencies)
- No side effects (no prints, logging, or I/O)
- Simplified control flow by replacing if-else with max()
- Preserved all edge cases (None handling, recursive structure)
- Maintained exact return types and values
- No algorithm changes (same recursive approach)
