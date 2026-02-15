# LRU Cache Implementation

This project implements a Least Recently Used (LRU) cache in Python using a doubly-linked list for O(1) access and a dictionary for O(1) lookups. The implementation is a standalone module with no external dependencies.

## Setup

1. Clone the repository
2. No additional dependencies are required (uses only Python standard library)

## Run

```bash
python -m src.main
```

## Example Usage

The demo in `src/main.py` shows the following operations:

1. Creating a cache with capacity 2
2. Putting values (1,1) and (2,2)
3. Getting value for key 1 (returns 1)
4. Putting value (3,3) which evicts key 2
5. Getting value for key 2 (returns -1 as it was evicted)

## Project Structure

```
.
├── README.md
├── requirements.txt
├── src/
│   └── main.py
└── tests/
    └── test_main.py
```

The implementation includes:
- `Node` class for doubly-linked list nodes
- `LRUCache` class with get/put operations
- Demo function showing cache behavior
- Unit tests for edge cases
