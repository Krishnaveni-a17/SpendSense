# app.py
# Main Flask application for the Expense Tracker API.
# Runs a web server that responds to HTTP requests.
# Today: foundation setup with health check endpoint.

from flask import Flask, jsonify

# Create the Flask application instance
# __name__ tells Flask where to find resources
# relative to this file
app = Flask(__name__)


@app.route("/", methods=["GET"])
def home():
    """
    Health check endpoint.
    Returns API status — used to confirm server is running.
    GET http://localhost:5000/
    """
    return jsonify({
        "status" : "running",
        "message": "Expense Tracker API is live",
        "version": "1.0",
        "endpoints": {
            "add expense"    : "POST /expenses",
            "view expenses"  : "GET  /expenses",
            "analyse"        : "GET  /expenses/analyse",
            "delete expense" : "DELETE /expenses/<id>"
        }
    }), 200


@app.route("/expenses", methods=["GET"])
def get_expenses():
    """
    Returns all expenses.
    Today: returns empty list as placeholder.
    Tomorrow: will query from SQLite database.
    GET http://localhost:5000/expenses
    """
    return jsonify({
        "status"  : "success",
        "count"   : 0,
        "expenses": []
    }), 200


@app.route("/expenses", methods=["POST"])
def add_expense():
    """
    Adds a new expense.
    Today: returns placeholder response.
    Tomorrow: will save to SQLite database.
    POST http://localhost:5000/expenses
    """
    return jsonify({
        "status" : "success",
        "message": "Expense endpoint ready — database coming tomorrow"
    }), 201


if __name__ == "__main__":
    # debug=True means:
    # 1. Server restarts automatically when you save changes
    # 2. Shows detailed error messages in the browser
    # NEVER use debug=True in production — only for development
    app.run(debug=True, port=5000)