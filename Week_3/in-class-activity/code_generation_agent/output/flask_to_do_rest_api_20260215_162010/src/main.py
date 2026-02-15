from flask import Flask, request, jsonify
from typing import List, Dict, Optional

app = Flask(__name__)

# In-memory data store
todos: List[Dict] = []

def generate_id() -> int:
    """Generate a unique ID for a new todo item."""
    return max((todo["id"] for todo in todos), default=0) + 1

def validate_todo(data: Dict) -> Dict:
    """Validate todo data and return cleaned version."""
    if "title" not in data or not isinstance(data["title"], str):
        raise ValueError("Title is required and must be a string")
    return {
        "id": data.get("id"),
        "title": data["title"].strip(),
        "done": data.get("done", False)
    }

def serialize_todo(todo: Dict) -> Dict:
    """Serialize todo item for JSON response."""
    return {
        "id": todo["id"],
        "title": todo["title"],
        "done": todo["done"]
    }

@app.route("/")
def index() -> str:
    """Root endpoint with API info."""
    return jsonify({
        "message": "Flask To-Do REST API",
        "endpoints": {
            "GET /todos": "List all todos",
            "POST /todos": "Create a new todo",
            "GET /todos/<id>": "Get a specific todo",
            "PUT /todos/<id>": "Update a todo",
            "DELETE /todos/<id>": "Delete a todo"
        }
    })

@app.route("/todos", methods=["GET"])
def get_todos() -> Dict:
    """Get all todos."""
    return jsonify([serialize_todo(todo) for todo in todos])

@app.route("/todos", methods=["POST"])
def create_todo() -> Dict:
    """Create a new todo."""
    try:
        data = request.get_json()
        if not data:
            raise ValueError("No JSON data provided")

        validated = validate_todo(data)
        if validated["id"] and any(t["id"] == validated["id"] for t in todos):
            raise ValueError("ID already exists")

        new_todo = {
            "id": validated["id"] or generate_id(),
            "title": validated["title"],
            "done": validated["done"]
        }
        todos.append(new_todo)
        return jsonify(serialize_todo(new_todo)), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@app.route("/todos/<int:todo_id>", methods=["GET"])
def get_todo(todo_id: int) -> Dict:
    """Get a specific todo by ID."""
    todo = next((t for t in todos if t["id"] == todo_id), None)
    if not todo:
        return jsonify({"error": "Todo not found"}), 404
    return jsonify(serialize_todo(todo))

@app.route("/todos/<int:todo_id>", methods=["PUT"])
def update_todo(todo_id: int) -> Dict:
    """Update a todo by ID."""
    try:
        data = request.get_json()
        if not data:
            raise ValueError("No JSON data provided")

        validated = validate_todo(data)
        todo = next((t for t in todos if t["id"] == todo_id), None)
        if not todo:
            return jsonify({"error": "Todo not found"}), 404

        todo.update({
            "title": validated["title"],
            "done": validated["done"]
        })
        return jsonify(serialize_todo(todo))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@app.route("/todos/<int:todo_id>", methods=["DELETE"])
def delete_todo(todo_id: int) -> Dict:
    """Delete a todo by ID."""
    global todos
    todo = next((t for t in todos if t["id"] == todo_id), None)
    if not todo:
        return jsonify({"error": "Todo not found"}), 404

    todos = [t for t in todos if t["id"] != todo_id]
    return jsonify({"message": "Todo deleted"}), 200

if __name__ == "__main__":
    app.run(debug=True)
