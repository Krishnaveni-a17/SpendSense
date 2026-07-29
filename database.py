# database.py
# Handles all SQLite database operations for SpendSense API.
# Separating database logic from route logic keeps code clean
# and makes testing and maintenance much easier.

import sqlite3
import os

# Path to the database file
# Lives inside data/ folder — same as your JSON files before
DATABASE = "data/expenses.db"


def get_connection():

    os.makedirs("data", exist_ok=True)
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():

    connection = get_connection()
    cursor     = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            amount   REAL    NOT NULL,
            category TEXT    NOT NULL,
            note     TEXT    NOT NULL,
            date     TEXT    NOT NULL
        )
    """)

    connection.commit()
    connection.close()
    print("Database initialised successfully.")


def insert_expense(amount, category, note, date):

    connection = get_connection()
    cursor     = connection.cursor()

    cursor.execute("""
        INSERT INTO expenses (amount, category, note, date)
        VALUES (?, ?, ?, ?)
    """, (amount, category, note, date))

    connection.commit()

    # lastrowid gives the auto-generated ID of the row just inserted
    new_id = cursor.lastrowid

    connection.close()
    return new_id


def fetch_all_expenses():

    connection = get_connection()
    cursor     = connection.cursor()

    cursor.execute("SELECT * FROM expenses ORDER BY date DESC")
    rows = cursor.fetchall()

    connection.close()

    # Convert each Row object to a plain dict
    return [dict(row) for row in rows]


def fetch_expense_by_id(expense_id):

    connection = get_connection()
    cursor     = connection.cursor()

    cursor.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,))
    row = cursor.fetchone()

    connection.close()

    if row is None:
        return None
    return dict(row)


def delete_expense(expense_id):

    connection = get_connection()
    cursor     = connection.cursor()

    cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    connection.commit()

    # rowcount tells how many rows were affected
    # 0 means no row with that ID existed
    deleted = cursor.rowcount > 0

    connection.close()
    return deleted

def update_expense(expense_id, fields):

    if not fields:
        return False

    # Build SET clause dynamically from provided fields
    # Example: {"amount": 500} → "amount = ?"
    set_clause = ", ".join(f"{col} = ?" for col in fields.keys())
    values     = list(fields.values()) + [expense_id]

    connection = get_connection()
    cursor     = connection.cursor()

    cursor.execute(
        f"UPDATE expenses SET {set_clause} WHERE id = ?",
        values
    )
    connection.commit()

    updated = cursor.rowcount > 0
    connection.close()
    return updated


def fetch_expenses_by_category(category):

    connection = get_connection()
    cursor     = connection.cursor()

    cursor.execute(
        "SELECT * FROM expenses WHERE category = ? ORDER BY date DESC",
        (category,)
    )
    rows = cursor.fetchall()
    connection.close()

    return [dict(row) for row in rows]