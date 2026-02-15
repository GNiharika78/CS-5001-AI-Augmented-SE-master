# Flask To-Do REST API

A minimal Flask REST API for CRUD operations on a to-do list.

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Run

Start the development server:
```bash
python -m src.main
```

The API will be available at `http://localhost:5000`.

## Example Usage

### Create a to-do item
```bash
curl -X POST -H "Content-Type: application/json" -d '{"title":"Buy groceries"}' http://localhost:5000/todos
```

### Get all to-do items
```bash
curl http://localhost:5000/todos
```

### Get a specific to-do item
```bash
curl http://localhost:5000/todos/1
```

### Update a to-do item
```bash
curl -X PUT -H "Content-Type: application/json" -d '{"title":"Buy groceries and milk", "done":true}' http://localhost:5000/todos/1
```

### Delete a to-do item
```bash
curl -X DELETE http://localhost:5000/todos/1
```

## Project Structure

```
.
├── README.md
├── requirements.txt
└── src
    └── main.py
