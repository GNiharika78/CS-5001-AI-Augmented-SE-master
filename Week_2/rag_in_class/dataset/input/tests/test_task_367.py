from tasks.task_367 import Node, is_tree_balanced

def build_unbalanced():
    root = Node(1)
    root.left = Node(2)
    root.left.left = Node(3)
    root.left.left.left = Node(4)
    return root

def build_balanced():
    root = Node(1)
    root.left = Node(2)
    root.right = Node(3)
    root.left.left = Node(4)
    root.left.right = Node(5)
    root.right.left = Node(6)
    root.right.right = Node(7)
    return root

root = build_unbalanced()
root1 = build_balanced()
root2 = build_unbalanced()

def test_mbpp_asserts():
    assert is_tree_balanced(root) == False
    assert is_tree_balanced(root1) == True
    assert is_tree_balanced(root2) == False
