# app.py
# Main Flask application for SpendSense API.
# Routes receive HTTP requests, call database functions,
# and return JSON responses with appropriate status codes.

from analyser import run_analysis
from flask  import Flask, jsonify, request
from database import init_db, insert_expense, fetch_all_expenses, \
                    fetch_expense_by_id, delete_expense

VALID_CATEGORIES = ["Food", "Transport", "Shopping",
                    "Utilities", "Subscriptions"]

app = Flask(__name__)


@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "status" : "running",
        "message": "SpendSense API is live",
        "version": "2.0",
        "endpoints": {
            "add expense"   : "POST   /expenses",
            "view all"      : "GET    /expenses",
            "delete expense": "DELETE /expenses/<id>",
            "analyse"       : "GET    /expenses/analyse"
        }
    }), 200


@app.route("/expenses", methods=["GET"])
def get_expenses():

    expenses = fetch_all_expenses()
    return jsonify({
        "status"  : "success",
        "count"   : len(expenses),
        "expenses": expenses
    }), 200


@app.route("/expenses", methods=["POST"])
def add_expense():

    data = request.get_json()

    # Validate request body exists
    if not data:
        return jsonify({
            "status": "error",
            "message": "Request body is missing or not JSON"
        }), 400

    # Validate all required fields are present
    required = ["amount", "category", "note", "date"]
    for field in required:
        if field not in data:
            return jsonify({
                "status" : "error",
                "message": f"Missing required field: '{field}'"
            }), 400

    # Validate amount is a positive number
    try:
        amount = float(data["amount"])
        if amount <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({
            "status" : "error",
            "message": "Amount must be a positive number"
        }), 400

    # Validate category
    category = str(data["category"]).strip().capitalize()
    if category not in VALID_CATEGORIES:
        return jsonify({
            "status" : "error",
            "message": f"Invalid category. Choose from: {VALID_CATEGORIES}"
        }), 400

    # Validate date format
    date = str(data["date"])
    if len(date) != 10 or date[4] != "-" or date[7] != "-":
        return jsonify({
            "status" : "error",
            "message": "Date must be in YYYY-MM-DD format"
        }), 400

    note = str(data["note"]).strip()
    if len(note) == 0:
        return jsonify({
            "status" : "error",
            "message": "Note cannot be empty"
        }), 400

    # All validation passed — save to database
    new_id = insert_expense(amount, category, note, date)

    return jsonify({
        "status" : "success",
        "message": "Expense added successfully",
        "expense": {
            "id"      : new_id,
            "amount"  : amount,
            "category": category,
            "note"    : note,
            "date"    : date
        }
    }), 201


@app.route("/expenses/<int:expense_id>", methods=["DELETE"])
def remove_expense(expense_id):

    expense = fetch_expense_by_id(expense_id)

    if expense is None:
        return jsonify({
            "status" : "error",
            "message": f"Expense with ID {expense_id} not found"
        }), 404

    delete_expense(expense_id)

    return jsonify({
        "status" : "success",
        "message": f"Expense {expense_id} deleted successfully"
    }), 200

@app.route("/expenses/analyse", methods=["GET"])
def analyse_expenses():

    expenses = fetch_all_expenses()

    if len(expenses) == 0:
        return jsonify({
            "status" : "error",
            "message": "No expenses found. Add some expenses first."
        }), 404

    analysis = run_analysis(expenses)

    return jsonify({
        "status"  : "success",
        "analysis": analysis
    }), 200
if __name__ == "__main__":
    init_db()      # create table if it doesn't exist
    app.run(debug=True, port=5000)