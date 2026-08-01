# SpendSense API

A REST API built with Python, Flask, and SQLite that tracks personal
expenses and analyses spending behaviour to classify your spending
personality type.

## Live API

Base URL: `https://spendsense-api.onrender.com`

> Note: Free tier sleeps after 15 min inactivity.
> First request may take 30-60 seconds to wake up.

---

## What Makes This Different

Most expense trackers just store numbers. SpendSense analyses
spending patterns and classifies behaviour:

- Groups expenses by category and calculates percentages
- Rule engine assigns personality type —
  Comfort Seeker, Impulse Buyer, Balanced Saver, etc.
- Generates personalised annual savings projection
- Rich statistics — highest, lowest, daily average, top category

---

## Tech Stack

| Technology | Purpose |
|------------|---------|
| Python 3.11 | Core language |
| Flask 3.1 | REST API framework |
| SQLite3 | Built-in database, zero setup |
| gunicorn | Production WSGI server |
| Render.com | Cloud deployment |
| Postman | API testing |

---

## Project Structure
SpendSense/
├── app.py → Flask routes, logging, error handlers
├── database.py → SQLite CRUD operations
├── analyser.py → Business logic — analysis engine
├── requirements.txt → Project dependencies
├── render.yaml → Render deployment configuration
├── data/
│ └── expenses.db → SQLite database
└── logs/
└── app.log → Persistent request logs

---

## Setup and Run Locally

```bash
git clone https://github.com/Krishnaveni-a17/SpendSense.git
cd SpendSense
pip install -r requirements.txt
python app.py
```

Server runs at `http://localhost:5000`

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| POST | `/expenses` | Add a new expense |
| GET | `/expenses` | Get all expenses |
| GET | `/expenses?category=Food` | Filter by category |
| GET | `/expenses?note=swiggy` | Search by keyword |
| PUT | `/expenses/<id>` | Partial update |
| DELETE | `/expenses/<id>` | Delete by ID |
| GET | `/expenses/analyse` | Spending personality analysis |
| GET | `/expenses/stats` | Rich statistics |

---

## Request Examples

### Add Expense
```json
POST /expenses
{
    "amount": 450,
    "category": "Food",
    "note": "Swiggy",
    "date": "2026-07-30"
}
```

### Analysis Response
```json
GET /expenses/analyse
{
    "analysis": {
        "personality": {
            "type": "Comfort Seeker",
            "description": "Over half your money goes to food..."
        },
        "breakdown": [
            {"category": "Food", "percentage": 33.5,
             "bar": "███████░░░░░░░░░░░░░"}
        ],
        "nudge": "Cut Food by 20% and save ₹1080.00 per year."
    }
}
```

---

## Error Responses

All errors return consistent JSON — never HTML:

```json
{
    "status": "error",
    "message": "Missing required field: 'category'",
    "code": 400
}
```

| Code | Meaning |
|------|---------|
| 400 | Invalid input or missing fields |
| 404 | Resource not found |
| 405 | Wrong HTTP method |
| 500 | Unexpected server error |

---

## Valid Categories

`Food` | `Transport` | `Shopping` | `Utilities` | `Subscriptions`

---

## Architecture — Three Layers

app.py → HTTP only — routes, validation, JSON responses
analyser.py → Business logic — pure Python, no Flask/database
database.py → Data layer — SQLite only, no Flask/logic

Swapping SQLite for PostgreSQL = only touch database.py.
Changing personality rules = only touch analyser.py.

---

## What I Learned

- Flask REST API with correct HTTP methods and status codes
- SQLite with parameterised queries — SQL injection prevention
- Three-layer architecture separating concerns
- Global error handlers — consistent JSON for all errors
- Python logging — persistent request tracking to file
- Query parameters for filtering without extra endpoints
- Partial update — only modify fields that are sent
- gunicorn WSGI server for production deployment
- Deploying to Render with auto-deploy from GitHub

---

