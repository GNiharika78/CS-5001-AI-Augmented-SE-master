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
