from __future__ import annotations
import sys
from typing import Any, Optional

class Node:
    """A doubly-linked list node holding a key-value pair."""
    def __init__(self, key: Any, value: Any) -> None:
        self.key = key
        self.value = value
        self.prev: Optional[Node] = None
        self.next: Optional[Node] = None

class LRUCache:
    """Least Recently Used cache with O(1) get/put using a doubly-linked list and a dictionary."""

    def __init__(self, capacity: int) -> None:
        """Initialize the cache with a given capacity.

        Args:
            capacity: Maximum number of items the cache can hold. Must be non-negative.
        """
        if capacity < 0:
            raise ValueError("Capacity must be non-negative")
        self.capacity = capacity
        self.cache: dict[Any, Node] = {}
        # Dummy head and tail to simplify boundary checks
        self.head = Node(None, None)  # Most recently used
        self.tail = Node(None, None)  # Least recently used
        self.head.next = self.tail
        self.tail.prev = self.head

    def _add_to_head(self, node: Node) -> None:
        """Add a node right after the dummy head (most recently used)."""
        node.prev = self.head
        node.next = self.head.next
        self.head.next.prev = node
        self.head.next = node

    def _remove_node(self, node: Node) -> None:
        """Remove a node from the linked list."""
        prev_node = node.prev
        next_node = node.next
        if prev_node:
            prev_node.next = next_node
        if next_node:
            next_node.prev = prev_node

    def _move_to_head(self, node: Node) -> None:
        """Move an existing node to the head (most recently used)."""
        self._remove_node(node)
        self._add_to_head(node)

    def _pop_tail(self) -> Optional[Node]:
        """Remove and return the node before the dummy tail (least recently used)."""
        if self.head.next == self.tail:
            return None
        node = self.tail.prev
        self._remove_node(node)
        return node

    def get(self, key: Any) -> Any:
        """Get the value associated with the key, moving it to the most recently used position.

        Args:
            key: The key to look up.

        Returns:
            The value associated with the key, or None if the key is not found.
        """
        if key not in self.cache:
            return None
        node = self.cache[key]
        self._move_to_head(node)
        return node.value

    def put(self, key: Any, value: Any) -> None:
        """Insert or update a key-value pair, evicting the least recently used item if capacity is exceeded.

        Args:
            key: The key to insert or update.
            value: The value to associate with the key.
        """
        if key in self.cache:
            node = self.cache[key]
            node.value = value
            self._move_to_head(node)
        else:
            if len(self.cache) >= self.capacity and self.capacity > 0:
                tail_node = self._pop_tail()
                if tail_node:
                    del self.cache[tail_node.key]
            new_node = Node(key, value)
            self.cache[key] = new_node
            self._add_to_head(new_node)

def print_demo() -> None:
    """Print deterministic outputs for a few cache operations."""
    print("LRU Cache Demo")
    print("--------------")
    cache = LRUCache(2)
    cache.put(1, 1)
    cache.put(2, 2)
    print("After put(1,1) and put(2,2):")
    print("  get(1) ->", cache.get(1))  # 1
    print("  get(2) ->", cache.get(2))  # 2
    cache.put(3, 3)
    print("After put(3,3):")
    print("  get(1) ->", cache.get(1))  # None (evicted)
    print("  get(2) ->", cache.get(2))  # 2
    print("  get(3) ->", cache.get(3))  # 3
    cache.put(4, 4)
    print("After put(4,4):")
    print("  get(2) ->", cache.get(2))  # None (evicted)
    print("  get(3) ->", cache.get(3))  # 3
    print("  get(4) ->", cache.get(4))  # 4
    print("--------------")

def main() -> None:
    """CLI entry point. Prints a demo if no arguments, otherwise runs interactive mode."""
    if len(sys.argv) == 1:
        print_demo()
    else:
        print("Interactive mode not implemented in this demo.")

if __name__ == "__main__":
    main()
