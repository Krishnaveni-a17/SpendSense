# app.py
# Main Flask application for SpendSense API.

import logging
import os
from flask    import Flask, jsonify, request
from database import (init_db, insert_expense, fetch_all_expenses,
                      fetch_expense_by_id, delete_expense,
                      update_expense, fetch_expenses_by_category,
                      search_expenses_by_note)
from analyser import run_analysis, calculate_stats

# ── LOGGING SETUP ─────────────────────────────────────────────────────────
# Configure before anything else so all events are captured.
# Writes to BOTH a file (app.log) AND the terminal simultaneously.

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level   = logging.INFO,
    format  = "%(asctime)s | %(levelname)s | %(message)s",
    datefmt = "%Y-%m-%d %H:%M:%S",
    handlers = [
        logging.FileHandler("logs/app.log", encoding="utf-8"),   # writes to file
        logging.StreamHandler()                 # also prints to terminal
    ]
)

logger = logging.getLogger(__name__)

VALID_CATEGORIES = ["Food", "Transport", "Shopping",
                    "Utilities", "Subscriptions"]

app = Flask(__name__)


# ── GLOBAL ERROR HANDLERS ─────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(error):
    logger.warning(f"404 Not Found: {request.method} {request.path}")
    return jsonify({
        "status" : "error",
        "message": "The requested resource was not found.",
        "code"   : 404
    }), 404


@app.errorhandler(405)
def method_not_allowed(error):
    logger.warning(f"405 Method Not Allowed: {request.method} {request.path}")
    return jsonify({
        "status" : "error",
        "message": "HTTP method not allowed for this endpoint.",
        "code"   : 405
    }), 405


@app.errorhandler(500)
def server_error(error):
    logger.error(f"500 Server Error: {request.method} {request.path} | {error}")
    return jsonify({
        "status" : "error",
        "message": "Something went wrong on our end. Please try again.",
        "code"   : 500
    }), 500


# ── ROUTES ────────────────────────────────────────────────────────────────

@app.route("/", methods=["GET"])
def home():
    logger.info("Health check requested")
    return jsonify({
        "status" : "running",
        "message": "SpendSense API is live",
        "version": "6.0",
        "endpoints": {
            "health check"   : "GET    /",
            "add expense"    : "POST   /expenses",
            "view all"       : "GET    /expenses",
            "filter category": "GET    /expenses?category=Food",
            "update expense" : "PUT    /expenses/<id>",
            "delete expense" : "DELETE /expenses/<id>",
            "analyse"        : "GET    /expenses/analyse",
            "statistics"     : "GET    /expenses/stats"
        }
    }), 200

@app.route("/expenses", methods=["GET"])
def get_expenses():

    category = request.args.get("category", None)
    note     = request.args.get("note", None)

    if category:
        category = category.strip().capitalize()
        if category not in VALID_CATEGORIES:
            logger.warning(f"GET /expenses — invalid category: {category}")
            return jsonify({
                "status" : "error",
                "message": f"Invalid category. Choose from: {VALID_CATEGORIES}"
            }), 400
        expenses = fetch_expenses_by_category(category)
        logger.info(f"GET /expenses?category={category} — {len(expenses)} results")
        return jsonify({
            "status"  : "success",
            "filter"  : f"category={category}",
            "count"   : len(expenses),
            "expenses": expenses
        }), 200

    if note:
        keyword  = note.strip()
        expenses = search_expenses_by_note(keyword)
        logger.info(f"GET /expenses?note={keyword} — {len(expenses)} results")
        return jsonify({
            "status"  : "success",
            "filter"  : f"note contains '{keyword}'",
            "count"   : len(expenses),
            "expenses": expenses
        }), 200

    expenses = fetch_all_expenses()
    logger.info(f"GET /expenses — returned {len(expenses)} expenses")
    return jsonify({
        "status"  : "success",
        "count"   : len(expenses),
        "expenses": expenses
    }), 200

@app.route("/expenses", methods=["POST"])
def add_expense():

    data = request.get_json()

    if not data:
        logger.warning("POST /expenses — missing or invalid JSON body")
        return jsonify({
            "status" : "error",
            "message": "Request body is missing or not JSON"
        }), 400

    required = ["amount", "category", "note", "date"]
    for field in required:
        if field not in data:
            logger.warning(f"POST /expenses — missing field: {field}")
            return jsonify({
                "status" : "error",
                "message": f"Missing required field: '{field}'"
            }), 400

    try:
        amount = float(data["amount"])
        if amount <= 0:
            raise ValueError
    except (ValueError, TypeError):
        logger.warning(f"POST /expenses — invalid amount: {data.get('amount')}")
        return jsonify({
            "status" : "error",
            "message": "Amount must be a positive number"
        }), 400

    category = str(data["category"]).strip().capitalize()
    if category not in VALID_CATEGORIES:
        logger.warning(f"POST /expenses — invalid category: {category}")
        return jsonify({
            "status" : "error",
            "message": f"Invalid category. Choose from: {VALID_CATEGORIES}"
        }), 400

    date = str(data["date"])
    if len(date) != 10 or date[4] != "-" or date[7] != "-":
        logger.warning(f"POST /expenses — invalid date format: {date}")
        return jsonify({
            "status" : "error",
            "message": "Date must be in YYYY-MM-DD format"
        }), 400

    note = str(data["note"]).strip()
    if len(note) == 0:
        logger.warning("POST /expenses — empty note")
        return jsonify({
            "status" : "error",
            "message": "Note cannot be empty"
        }), 400

    new_id = insert_expense(amount, category, note, date)
    logger.info(f"POST /expenses — created expense ID {new_id}: "
                f"₹{amount} {category} ({note})")

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


@app.route("/expenses/<int:expense_id>", methods=["PUT"])
def edit_expense(expense_id):

    expense = fetch_expense_by_id(expense_id)
    if expense is None:
        logger.warning(f"PUT /expenses/{expense_id} — not found")
        return jsonify({
            "status" : "error",
            "message": f"Expense with ID {expense_id} not found"
        }), 404

    data = request.get_json()
    if not data:
        return jsonify({
            "status" : "error",
            "message": "Request body is missing or not JSON"
        }), 400

    updated_fields = {}

    if "amount" in data:
        try:
            amount = float(data["amount"])
            if amount <= 0:
                raise ValueError
            updated_fields["amount"] = amount
        except (ValueError, TypeError):
            return jsonify({
                "status" : "error",
                "message": "Amount must be a positive number"
            }), 400

    if "category" in data:
        category = str(data["category"]).strip().capitalize()
        if category not in VALID_CATEGORIES:
            return jsonify({
                "status" : "error",
                "message": f"Invalid category. Choose from: {VALID_CATEGORIES}"
            }), 400
        updated_fields["category"] = category

    if "note" in data:
        note = str(data["note"]).strip()
        if len(note) == 0:
            return jsonify({
                "status" : "error",
                "message": "Note cannot be empty"
            }), 400
        updated_fields["note"] = note

    if "date" in data:
        date = str(data["date"])
        if len(date) != 10 or date[4] != "-" or date[7] != "-":
            return jsonify({
                "status" : "error",
                "message": "Date must be in YYYY-MM-DD format"
            }), 400
        updated_fields["date"] = date

    if not updated_fields:
        return jsonify({
            "status" : "error",
            "message": "No valid fields provided to update"
        }), 400

    update_expense(expense_id, updated_fields)
    logger.info(f"PUT /expenses/{expense_id} — updated fields: "
                f"{list(updated_fields.keys())}")

    updated = fetch_expense_by_id(expense_id)
    return jsonify({
        "status"        : "success",
        "message"       : f"Expense {expense_id} updated successfully",
        "updated_fields": list(updated_fields.keys()),
        "expense"       : updated
    }), 200


@app.route("/expenses/<int:expense_id>", methods=["DELETE"])
def remove_expense(expense_id):

    expense = fetch_expense_by_id(expense_id)
    if expense is None:
        logger.warning(f"DELETE /expenses/{expense_id} — not found")
        return jsonify({
            "status" : "error",
            "message": f"Expense with ID {expense_id} not found"
        }), 404

    delete_expense(expense_id)
    logger.info(f"DELETE /expenses/{expense_id} — deleted successfully")

    return jsonify({
        "status" : "success",
        "message": f"Expense {expense_id} deleted successfully"
    }), 200


@app.route("/expenses/analyse", methods=["GET"])
def analyse_expenses():

    expenses = fetch_all_expenses()
    if len(expenses) == 0:
        logger.warning("GET /expenses/analyse — no expenses found")
        return jsonify({
            "status" : "error",
            "message": "No expenses found. Add some first."
        }), 404

    analysis = run_analysis(expenses)
    logger.info(f"GET /expenses/analyse — personality: "
                f"{analysis['personality']['type']}")
    return jsonify({
        "status"  : "success",
        "analysis": analysis
    }), 200


@app.route("/expenses/stats", methods=["GET"])
def expense_stats():

    expenses = fetch_all_expenses()
    if len(expenses) == 0:
        logger.warning("GET /expenses/stats — no expenses found")
        return jsonify({
            "status" : "error",
            "message": "No expenses found. Add some first."
        }), 404

    stats = calculate_stats(expenses)
    logger.info(f"GET /expenses/stats — total: ₹{stats['total_spent']}, "
                f"count: {stats['expense_count']}")
    return jsonify({
        "status": "success",
        "stats" : stats
    }), 200


if __name__ == "__main__":
    logger.info("SpendSense API starting up...")
    init_db()
    logger.info("Database initialised. Server ready.")
    app.run(debug=True, port=5000)