from tasks.task_927 import Node, max_height

def build_height(h):
    # Build a left-leaning chain with height h (number of nodes on longest path).
    if h <= 0:
        return None
    root = Node(0)
    cur = root
    for i in range(1, h):
        cur.left = Node(i)
        cur = cur.left
    return root

root = build_height(3)
root1 = build_height(5)
root2 = build_height(4)

def test_mbpp_asserts():
    assert (max_height(root)) == 3
    assert (max_height(root1)) == 5
    assert (max_height(root2)) == 4
