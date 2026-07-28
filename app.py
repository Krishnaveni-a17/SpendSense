# app.py
# Main Flask application for SpendSense API.
# HTTP layer only — receives requests, calls modules, returns JSON.


from flask    import Flask, jsonify, request
from database import (init_db, insert_expense, fetch_all_expenses,
                      fetch_expense_by_id, delete_expense)
from analyser import run_analysis, calculate_stats

VALID_CATEGORIES = ["Food", "Transport", "Shopping",
                    "Utilities", "Subscriptions"]

app = Flask(__name__)


# ── GLOBAL ERROR HANDLERS ─────────────────────────────────────────────────
# These catch errors anywhere in the app — not just in one route.
# Return consistent JSON instead of Flask's default HTML error pages.

@app.errorhandler(404)
def not_found(error):

    return jsonify({
        "status" : "error",
        "message": "The requested resource was not found.",
        "code"   : 404
    }), 404


@app.errorhandler(405)
def method_not_allowed(error):

    return jsonify({
        "status" : "error",
        "message": "HTTP method not allowed for this endpoint.",
        "code"   : 405
    }), 405


@app.errorhandler(500)
def server_error(error):

    return jsonify({
        "status" : "error",
        "message": "Something went wrong on our end. Please try again.",
        "code"   : 500
    }), 500


# ── ROUTES ────────────────────────────────────────────────────────────────

@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "status" : "running",
        "message": "SpendSense API is live",
        "version": "4.0",
        "endpoints": {
            "health check"  : "GET    /",
            "add expense"   : "POST   /expenses",
            "view all"      : "GET    /expenses",
            "delete expense": "DELETE /expenses/<id>",
            "analyse"       : "GET    /expenses/analyse",
            "statistics"    : "GET    /expenses/stats"
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

    if not data:
        return jsonify({
            "status" : "error",
            "message": "Request body is missing or not JSON"
        }), 400

    required = ["amount", "category", "note", "date"]
    for field in required:
        if field not in data:
            return jsonify({
                "status" : "error",
                "message": f"Missing required field: '{field}'"
            }), 400

    try:
        amount = float(data["amount"])
        if amount <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({
            "status" : "error",
            "message": "Amount must be a positive number"
        }), 400

    category = str(data["category"]).strip().capitalize()
    if category not in VALID_CATEGORIES:
        return jsonify({
            "status" : "error",
            "message": f"Invalid category. Choose from: {VALID_CATEGORIES}"
        }), 400

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
            "message": "No expenses found. Add some first."
        }), 404

    analysis = run_analysis(expenses)

    return jsonify({
        "status"  : "success",
        "analysis": analysis
    }), 200


@app.route("/expenses/stats", methods=["GET"])
def expense_stats():

    expenses = fetch_all_expenses()

    if len(expenses) == 0:
        return jsonify({
            "status" : "error",
            "message": "No expenses found. Add some first."
        }), 404

    stats = calculate_stats(expenses)

    return jsonify({
        "status": "success",
        "stats" : stats
    }), 200


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)