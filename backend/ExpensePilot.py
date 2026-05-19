from datetime import datetime

from flask import Flask, request, render_template, redirect
from flask_sqlalchemy import SQLAlchemy
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=r"C:\dev\ExpensePilot\.env")

DATABASE_URL = os.getenv("DATABASE_URL")

print("DATABASE_URL =", DATABASE_URL)

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 
app = Flask(__name__,
            template_folder=os.path.join(BASE_DIR, "../templates"),
            static_folder=os.path.join(BASE_DIR, "../static")
        )

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://",
        "postgresql+psycopg2://"
    )

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    date = db.Column(db.DateTime, default=lambda:datetime.now(ZoneInfo("America/Chicago")))

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False, default=0.0)

CATEGORIES = [
    "food",
    "automotive",
    "entertainment",
    "utilities",
    "miscellaneous",
    "groceries",
    "housing",
    "bills",
    "insurance",
    "child care",
    "shopping"
]

def get_current_budget():
    budget_record = Budget.query.first()
    if budget_record is None:
        budget_record = Budget(amount=0.0)
        db.session.add(budget_record)
        db.session.commit()
    return budget_record.amount

@app.route("/dashboard")
def dashboard():     
    transactions = Transaction.query.all()
    category_totals = {category: 0 for category in CATEGORIES}

    for category in CATEGORIES:
        total = sum(
            tx.amount for tx in transactions
            if tx.category == category
        )
        category_totals[category] = total

    recent_transactions = list(reversed(transactions[-10:]))

    return render_template(
        "dashboard.html",
        category_totals=category_totals,
        recent_transactions=recent_transactions
    )
    
@app.route("/add", methods=["POST", "GET"])
def add_transaction():
    message = None

    if request.method == "POST":
        data = request.form
        amount = data.get("amount")
        category = data.get("category")
        date_str = data.get("date")
        description = data.get("description")
    
        if not data or "amount" not in data or "category" not in data:
            return {"error": "Invalid input. Please provide 'amount' and 'category'."}, 400
        
        if data["category"] not in CATEGORIES:
            return {"error": "Invalid category"}, 400
        try:
            amount = float(data["amount"])
        except ValueError:
            return {"error": "Amount must be a number."}, 400
        if date_str:
            try:
                date_value = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=ZoneInfo("America/Chicago"))
            except ValueError:
                return {"error": "Invalid date format. Use YYYY-MM-DD."}, 400
        else:
            date_value = datetime.now(ZoneInfo("America/Chicago"))
        if not description:
            return {"error": "Description cannot be empty."}, 400
        transaction = Transaction(
            amount = amount,
            category = category,
            description = description,
            date = date_value
        )
        db.session.add(transaction)
        db.session.commit()

        message = "Transaction added successfully!"
    return render_template("add_transactions.html", CATEGORIES=CATEGORIES, message=message)

@app.route("/transactions")
def get_transactions():
    transactions = Transaction.query.all()
    return render_template(
        "view-transactions.html",
        title="All Transactions",
        transactions=transactions
    )

@app.route("/categories")
def categories():
    return render_template("categories.html", categories=CATEGORIES)

@app.route("/categories/<category>")
def get_transactions_by_category(category):
    if category not in CATEGORIES:
        return {"error": "Invalid category."}, 400
    filtered_transactions = Transaction.query.filter_by(category=category).all()
    total_spent = sum(tx.amount for tx in filtered_transactions)
    return render_template("category.html", category=category, transactions=filtered_transactions, total_spent=total_spent)

@app.route("/set_budget", methods=["POST"])
def set_budget():
    budget_value = request.form.get("budget")
    try:
        budget_value = float(budget_value)
    except (TypeError, ValueError):
        return {"error": "Invalid budget amount."}, 400

    budget_record = Budget.query.first()
    if budget_record is None:
        budget_record = Budget(amount=budget_value)
        db.session.add(budget_record)
    else:
        budget_record.amount = budget_value
    db.session.commit()

    return redirect("/budget")

@app.route("/budget", methods=["GET"])
def get_budget():
    budget_value = get_current_budget()
    transactions = Transaction.query.all()
    total_spent = sum(t.amount for t in transactions)
    remaining = budget_value - total_spent

    if total_spent > budget_value:
        message = "You are over your budget. Try reducing non-essential spending."
    elif total_spent > budget_value * 0.8:
        message = "You're close to your budget limit. Let's be weary of the spending!"
    else:
        message = "You're doing phenomenal! Keep up the good work!"
    
    return render_template("budget.html", budget=budget_value, total_spent=total_spent, remaining=remaining, message=message)

@app.route("/monthly")
def view_monthly_spending():
    selected_date = request.args.get("date")
    selected_month = request.args.get("month")

    transactions = Transaction.query.all()

    if selected_date:
        try:
            datetime.strptime(selected_date, "%Y-%m-%d")
        except ValueError:
            return {"error": "Invalid date format. Use YYYY-MM-DD."}, 400
        current_period = selected_date
        monthly_transactions = [t for t in transactions if t.date.strftime("%Y-%m-%d") == selected_date]
    else:
        if selected_month:
            try:
                datetime.strptime(selected_month, "%Y-%m")
            except ValueError:
                return {"error": "Invalid month format. Use YYYY-MM."}, 400
        else:
            selected_month = datetime.now(ZoneInfo("America/Chicago")).strftime("%Y-%m")
        current_period = selected_month
        monthly_transactions = [t for t in transactions if t.date.strftime("%Y-%m") == selected_month]

    total = sum(t.amount for t in monthly_transactions)

    return render_template(
        "monthly.html",
        month=current_period,
        total_spent=total,
        transactions=monthly_transactions,
        selected_month=selected_month,
        selected_date=selected_date,
    )

@app.route("/reset", methods=["GET", "POST"])
def reset_database():
    db.session.query(Transaction).delete()
    db.session.commit()
    return "Database cleared"

with app.app_context():
    db.create_all()
    if Budget.query.first() is None:
            db.session.add(Budget(amount=0.0))
            db.session.commit()

if __name__ == "__main__":
    app.run(debug=True)
