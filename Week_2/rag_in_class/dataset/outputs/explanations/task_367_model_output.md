# Model output for task_367

## Model
- devstral-small-2:24b-cloud

## Original Code:

class Node: 
	def __init__(self, data): 
		self.data = data 
		self.left = None
		self.right = None
def get_height(root): 
	if root is None: 
		return 0
	return max(get_height(root.left), get_height(root.right)) + 1
def is_tree_balanced(root): 
	if root is None: 
		return True
	lh = get_height(root.left) 
	rh = get_height(root.right) 
	if (abs(lh - rh) <= 1) and is_tree_balanced( 
	root.left) is True and is_tree_balanced( root.right) is True: 
		return True
	return False

## Refactored Code:

```python
class Node:
    def __init__(self, data):
        self.data = data
        self.left = None
        self.right = None

def get_height(root):
    if root is None:
        return 0
    return max(get_height(root.left), get_height(root.right)) + 1

def is_tree_balanced(root):
    if root is None:
        return True
    left_height = get_height(root.left)
    right_height = get_height(root.right)
    if (abs(left_height - right_height) <= 1) and is_tree_balanced(root.left) and is_tree_balanced(root.right):
        return True
    return False
```

- Preserved all function names, parameters, and return types exactly as in the original
- Maintained the same logic for height calculation and balance checking
- Kept the recursive approach for both height calculation and balance checking
- Preserved the exact same edge case handling (None returns True for balance)
- Did not introduce any new dependencies or side effects
- Improved readability by renaming variables (lh → left_height, rh → right_height)
- Maintained the same control flow structure while making it slightly cleaner
- Kept all functions at module scope as required
- Preserved the exact same behavior for all test cases
