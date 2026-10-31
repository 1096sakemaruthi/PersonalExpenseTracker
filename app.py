import os
import math
from datetime import date
from functools import wraps

from dotenv import load_dotenv
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
)
from werkzeug.security import generate_password_hash, check_password_hash

from db import get_db_connection

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

if not app.secret_key:
    raise RuntimeError(
        "FLASK_SECRET_KEY is missing. Add it to your .env file."
    )


# --------------------------------------------------
# LOGIN REQUIRED
# --------------------------------------------------

def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.")
            return redirect(url_for("login"))

        return view(*args, **kwargs)

    return wrapped_view


# --------------------------------------------------
# REGISTER
# --------------------------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password:
            flash("Please fill in all required fields.")
            return redirect(url_for("register"))

        if len(password) < 8:
            flash("Password must contain at least 8 characters.")
            return redirect(url_for("register"))

        if password != confirm_password:
            flash("Passwords do not match.")
            return redirect(url_for("register"))

        connection = get_db_connection()

        if connection is None:
            flash("Database connection failed. Please try again.")
            return redirect(url_for("register"))

        cursor = None

        try:
            cursor = connection.cursor(dictionary=True)

            cursor.execute("SELECT COUNT(*) AS total_users FROM users")
            user_count = cursor.fetchone()["total_users"]
            is_first_user = user_count == 0

            cursor.execute(
                "SELECT id FROM users WHERE email = %s",
                (email,),
            )

            if cursor.fetchone():
                connection.rollback()
                flash("This email is already registered. Please log in.")
                return redirect(url_for("login"))

            password_hash = generate_password_hash(password)

            cursor.execute(
                """
                INSERT INTO users (name, email, password_hash)
                VALUES (%s, %s, %s)
                """,
                (name, email, password_hash),
            )

            user_id = cursor.lastrowid

            if is_first_user:
                cursor.execute(
                    """
                    UPDATE expenses
                    SET user_id = %s
                    WHERE user_id IS NULL
                    """,
                    (user_id,),
                )

                cursor.execute(
                    """
                    UPDATE income
                    SET user_id = %s
                    WHERE user_id IS NULL
                    """,
                    (user_id,),
                )

            connection.commit()

            flash("Account created successfully. Please log in.")
            return redirect(url_for("login"))

        except Exception:
            connection.rollback()
            app.logger.exception("Registration failed.")
            flash("Registration failed. Please try again.")

        finally:
            if cursor is not None:
                cursor.close()
            connection.close()

    return render_template("register.html")


# --------------------------------------------------
# LOGIN
# --------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please enter your email and password.")
            return redirect(url_for("login"))

        connection = get_db_connection()

        if connection is None:
            flash("Database connection failed. Please try again.")
            return redirect(url_for("login"))

        cursor = None

        try:
            cursor = connection.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT id, name, email, password_hash
                FROM users
                WHERE email = %s
                """,
                (email,),
            )

            user = cursor.fetchone()

            if user and check_password_hash(
                user["password_hash"], password
            ):
                session.clear()
                session["user_id"] = user["id"]
                session["user_name"] = user["name"]

                return redirect(url_for("index"))

            flash("Invalid email or password.")

        except Exception:
            app.logger.exception("Login failed.")
            flash("Login failed. Please try again.")

        finally:
            if cursor is not None:
                cursor.close()
            connection.close()

    return render_template("login.html")


# --------------------------------------------------
# LOGOUT
# --------------------------------------------------

@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("login"))


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

@app.route("/")
@login_required
def index():
    user_id = session["user_id"]
    connection = get_db_connection()

    if connection is None:
        flash("Database connection failed.")
        return render_template(
            "index.html",
            expenses=[],
            incomes=[],
            transactions=[],
            total_income=0,
            total_expenses=0,
            total_balance=0,
            monthly_labels=[],
            monthly_expenses=[],
            monthly_income=[],
            monthly_data=[],
            user_name=session.get("user_name", ""),
        )

    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, title, amount, category, description, expense_date
            FROM expenses
            WHERE user_id = %s
            ORDER BY expense_date DESC, id DESC
            """,
            (user_id,),
        )
        expenses = cursor.fetchall()

        cursor.execute(
            """
            SELECT id, title, amount, source, description, income_date
            FROM income
            WHERE user_id = %s
            ORDER BY income_date DESC, id DESC
            """,
            (user_id,),
        )
        incomes = cursor.fetchall()

        cursor.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS total_expenses
            FROM expenses
            WHERE user_id = %s
            """,
            (user_id,),
        )
        total_expenses = cursor.fetchone()["total_expenses"]

        cursor.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS total_income
            FROM income
            WHERE user_id = %s
            """,
            (user_id,),
        )
        total_income = cursor.fetchone()["total_income"]

        total_balance = total_income - total_expenses

        cursor.execute(
            """
            SELECT
                DATE_FORMAT(expense_date, '%Y-%m') AS month_key,
                COALESCE(SUM(amount), 0) AS monthly_total
            FROM expenses
            WHERE user_id = %s
              AND expense_date >= DATE_FORMAT(
                    DATE_SUB(CURDATE(), INTERVAL 5 MONTH),
                    '%Y-%m-01'
                  )
              AND expense_date < DATE_ADD(
                    LAST_DAY(CURDATE()),
                    INTERVAL 1 DAY
                  )
            GROUP BY DATE_FORMAT(expense_date, '%Y-%m')
            """,
            (user_id,),
        )
        expense_rows = cursor.fetchall()

        cursor.execute(
            """
            SELECT
                DATE_FORMAT(income_date, '%Y-%m') AS month_key,
                COALESCE(SUM(amount), 0) AS monthly_total
            FROM income
            WHERE user_id = %s
              AND income_date >= DATE_FORMAT(
                    DATE_SUB(CURDATE(), INTERVAL 5 MONTH),
                    '%Y-%m-01'
                  )
              AND income_date < DATE_ADD(
                    LAST_DAY(CURDATE()),
                    INTERVAL 1 DAY
                  )
            GROUP BY DATE_FORMAT(income_date, '%Y-%m')
            """,
            (user_id,),
        )
        income_rows = cursor.fetchall()

        expense_by_month = {
            row["month_key"]: float(row["monthly_total"])
            for row in expense_rows
        }

        income_by_month = {
            row["month_key"]: float(row["monthly_total"])
            for row in income_rows
        }

        monthly_labels = []
        monthly_expenses = []
        monthly_income = []
        monthly_data = []

        current_month = date.today().replace(day=1)

        for offset in range(5, -1, -1):
            month_number = current_month.month - offset
            year = current_month.year

            while month_number <= 0:
                month_number += 12
                year -= 1

            month_date = date(year, month_number, 1)
            month_key = month_date.strftime("%Y-%m")
            month_label = month_date.strftime("%b %Y")

            month_expenses = expense_by_month.get(month_key, 0)
            month_income = income_by_month.get(month_key, 0)

            monthly_labels.append(month_label)
            monthly_expenses.append(month_expenses)
            monthly_income.append(month_income)

            monthly_data.append({
                "month": month_label,
                "income": month_income,
                "expenses": month_expenses,
            })

        # Combine income and expenses for recent activity.
        transactions = []

        for expense in expenses:
            transactions.append({
                "id": expense["id"],
                "title": expense["title"],
                "amount": expense["amount"],
                "category": expense["category"],
                "transaction_date": expense["expense_date"],
                "type": "expense",
            })

        for income in incomes:
            transactions.append({
                "id": income["id"],
                "title": income["title"],
                "amount": income["amount"],
                "category": income["source"],
                "transaction_date": income["income_date"],
                "type": "income",
            })

        transactions.sort(
            key=lambda item: (
                item["transaction_date"],
                item["id"]
            ),
            reverse=True,
        )

        return render_template(
            "index.html",
            expenses=expenses,
            incomes=incomes,
            transactions=transactions[:10],
            total_income=total_income,
            total_expenses=total_expenses,
            total_balance=total_balance,
            monthly_labels=monthly_labels,
            monthly_expenses=monthly_expenses,
            monthly_income=monthly_income,
            monthly_data=monthly_data,
            user_name=session.get("user_name", ""),
        )

    except Exception:
        app.logger.exception("Dashboard loading failed.")
        flash("Could not load the dashboard. Please try again.")

        return render_template(
            "index.html",
            expenses=[],
            incomes=[],
            transactions=[],
            total_income=0,
            total_expenses=0,
            total_balance=0,
            monthly_labels=[],
            monthly_expenses=[],
            monthly_income=[],
            monthly_data=[],
            user_name=session.get("user_name", ""),
        )

    finally:
        if cursor is not None:
            cursor.close()
        connection.close()


# --------------------------------------------------
# ADD EXPENSE
# --------------------------------------------------

@app.route("/add-expense", methods=["GET", "POST"])
@login_required
def add_expense():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        amount = request.form.get("amount", "").strip()
        category = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()
        expense_date = request.form.get("expense_date", "").strip()

        if not title or not amount or not category or not expense_date:
            flash("Please fill in all required fields.")
            return redirect(url_for("add_expense"))

        try:
            amount = float(amount)

            if not math.isfinite(amount) or amount <= 0:
                raise ValueError

            expense_date = date.fromisoformat(expense_date)

        except (ValueError, TypeError):
            flash("Enter a valid positive amount and date.")
            return redirect(url_for("add_expense"))

        connection = get_db_connection()

        if connection is None:
            flash("Database connection failed.")
            return redirect(url_for("add_expense"))

        cursor = None

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO expenses
                    (title, amount, category, description, expense_date, user_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    title,
                    amount,
                    category,
                    description,
                    expense_date,
                    session["user_id"],
                ),
            )

            connection.commit()
            flash("Expense added successfully.")
            return redirect(url_for("index"))

        except Exception:
            connection.rollback()
            app.logger.exception("Adding expense failed.")
            flash("Could not add expense. Please try again.")

        finally:
            if cursor is not None:
                cursor.close()
            connection.close()

    return render_template("add_expense.html")


# --------------------------------------------------
# ADD INCOME
# --------------------------------------------------

@app.route("/add-income", methods=["GET", "POST"])
@login_required
def add_income():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        source = request.form.get("source", "").strip()
        amount = request.form.get("amount", "").strip()
        description = request.form.get("description", "").strip()
        income_date = request.form.get("income_date", "").strip()

        if not title or not source or not amount or not income_date:
            flash("Please fill in all required fields.")
            return redirect(url_for("add_income"))

        try:
            amount = float(amount)

            if not math.isfinite(amount) or amount <= 0:
                raise ValueError

            income_date = date.fromisoformat(income_date)

        except (ValueError, TypeError):
            flash("Enter a valid positive amount and date.")
            return redirect(url_for("add_income"))

        connection = get_db_connection()

        if connection is None:
            flash("Database connection failed.")
            return redirect(url_for("add_income"))

        cursor = None

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO income
                    (title, amount, source, description, income_date, user_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    title,
                    amount,
                    source,
                    description,
                    income_date,
                    session["user_id"],
                ),
            )

            connection.commit()
            flash("Income added successfully.")
            return redirect(url_for("index"))

        except Exception:
            connection.rollback()
            app.logger.exception("Adding income failed.")
            flash("Could not add income. Please try again.")

        finally:
            if cursor is not None:
                cursor.close()
            connection.close()

    return render_template("add_income.html")


# --------------------------------------------------
# VIEW ALL INCOME
# --------------------------------------------------

@app.route("/incomes")
@app.route("/income-history")
@login_required
def income_list():
    connection = get_db_connection()

    if connection is None:
        flash("Database connection failed.")
        return redirect(url_for("index"))

    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, title, amount, source, description, income_date
            FROM income
            WHERE user_id = %s
            ORDER BY income_date DESC, id DESC
            """,
            (session["user_id"],),
        )

        incomes = cursor.fetchall()

        cursor.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS total_income
            FROM income
            WHERE user_id = %s
            """,
            (session["user_id"],),
        )

        total_income = cursor.fetchone()["total_income"]

        return render_template(
            "income_list.html",
            incomes=incomes,
            total_income=total_income,
        )

    except Exception:
        app.logger.exception("Loading income records failed.")
        flash("Could not load income records.")
        return redirect(url_for("index"))

    finally:
        if cursor is not None:
            cursor.close()
        connection.close()


# --------------------------------------------------
# EDIT INCOME
# --------------------------------------------------

@app.route("/edit-income/<int:income_id>", methods=["GET", "POST"])
@login_required
def edit_income(income_id):
    user_id = session["user_id"]
    connection = get_db_connection()

    if connection is None:
        flash("Database connection failed.")
        return redirect(url_for("income_list"))

    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, title, amount, source, description, income_date
            FROM income
            WHERE id = %s AND user_id = %s
            """,
            (income_id, user_id),
        )

        income = cursor.fetchone()

        if not income:
            flash("Income record not found.")
            return redirect(url_for("income_list"))

        if request.method == "POST":
            title = request.form.get("title", "").strip()
            source = request.form.get("source", "").strip()
            amount = request.form.get("amount", "").strip()
            description = request.form.get("description", "").strip()
            income_date = request.form.get("income_date", "").strip()

            if not title or not source or not amount or not income_date:
                flash("Please fill in all required fields.")
                return redirect(
                    url_for("edit_income", income_id=income_id)
                )

            try:
                amount = float(amount)

                if not math.isfinite(amount) or amount <= 0:
                    raise ValueError

                income_date = date.fromisoformat(income_date)

            except (ValueError, TypeError):
                flash("Enter a valid positive amount and date.")
                return redirect(
                    url_for("edit_income", income_id=income_id)
                )

            cursor.execute(
                """
                UPDATE income
                SET title = %s,
                    source = %s,
                    amount = %s,
                    description = %s,
                    income_date = %s
                WHERE id = %s AND user_id = %s
                """,
                (
                    title,
                    source,
                    amount,
                    description,
                    income_date,
                    income_id,
                    user_id,
                ),
            )

            connection.commit()
            flash("Income updated successfully.")
            return redirect(url_for("income_list"))

        return render_template("edit_income.html", income=income)

    except Exception:
        connection.rollback()
        app.logger.exception("Editing income failed.")
        flash("Could not edit income. Please try again.")
        return redirect(url_for("income_list"))

    finally:
        if cursor is not None:
            cursor.close()
        connection.close()


# --------------------------------------------------
# DELETE INCOME
# --------------------------------------------------

@app.route("/delete-income/<int:income_id>", methods=["POST"])
@login_required
def delete_income(income_id):
    connection = get_db_connection()

    if connection is None:
        flash("Database connection failed.")
        return redirect(url_for("income_list"))

    cursor = None

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM income
            WHERE id = %s AND user_id = %s
            """,
            (income_id, session["user_id"]),
        )

        connection.commit()

        if cursor.rowcount:
            flash("Income deleted successfully.")
        else:
            flash("Income record not found.")

    except Exception:
        connection.rollback()
        app.logger.exception("Deleting income failed.")
        flash("Could not delete income. Please try again.")

    finally:
        if cursor is not None:
            cursor.close()
        connection.close()

    return redirect(url_for("income_list"))


# --------------------------------------------------
# EDIT EXPENSE
# --------------------------------------------------

@app.route("/edit-expense/<int:expense_id>", methods=["GET", "POST"])
@login_required
def edit_expense(expense_id):
    user_id = session["user_id"]
    connection = get_db_connection()

    if connection is None:
        flash("Database connection failed.")
        return redirect(url_for("index"))

    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, title, amount, category, description, expense_date
            FROM expenses
            WHERE id = %s AND user_id = %s
            """,
            (expense_id, user_id),
        )
        expense = cursor.fetchone()

        if not expense:
            flash("Expense not found.")
            return redirect(url_for("index"))

        if request.method == "POST":
            title = request.form.get("title", "").strip()
            amount = request.form.get("amount", "").strip()
            category = request.form.get("category", "").strip()
            description = request.form.get("description", "").strip()
            expense_date = request.form.get("expense_date", "").strip()

            if not title or not amount or not category or not expense_date:
                flash("Please fill in all required fields.")
                return redirect(url_for("edit_expense", expense_id=expense_id))

            try:
                amount = float(amount)

                if not math.isfinite(amount) or amount <= 0:
                    raise ValueError

                expense_date = date.fromisoformat(expense_date)

            except (ValueError, TypeError):
                flash("Enter a valid positive amount and date.")
                return redirect(url_for("edit_expense", expense_id=expense_id))

            cursor.execute(
                """
                UPDATE expenses
                SET title = %s,
                    amount = %s,
                    category = %s,
                    description = %s,
                    expense_date = %s
                WHERE id = %s AND user_id = %s
                """,
                (
                    title,
                    amount,
                    category,
                    description,
                    expense_date,
                    expense_id,
                    user_id,
                ),
            )

            connection.commit()
            flash("Expense updated successfully.")
            return redirect(url_for("index"))

        return render_template("edit_expense.html", expense=expense)

    except Exception:
        connection.rollback()
        app.logger.exception("Editing expense failed.")
        flash("Could not edit expense. Please try again.")
        return redirect(url_for("index"))

    finally:
        if cursor is not None:
            cursor.close()
        connection.close()


# --------------------------------------------------
# DELETE EXPENSE
# --------------------------------------------------

@app.route("/delete-expense/<int:expense_id>", methods=["POST"])
@login_required
def delete_expense(expense_id):
    connection = get_db_connection()

    if connection is None:
        flash("Database connection failed.")
        return redirect(url_for("index"))

    cursor = None

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM expenses
            WHERE id = %s AND user_id = %s
            """,
            (expense_id, session["user_id"]),
        )

        connection.commit()

        if cursor.rowcount:
            flash("Expense deleted successfully.")
        else:
            flash("Expense not found.")

    except Exception:
        connection.rollback()
        app.logger.exception("Deleting expense failed.")
        flash("Could not delete expense. Please try again.")

    finally:
        if cursor is not None:
            cursor.close()
        connection.close()

    return redirect(url_for("index"))


# --------------------------------------------------
# MONTHLY REPORT
# --------------------------------------------------

@app.route("/monthly-report")
@login_required
def monthly_report():
    selected_month = request.args.get(
        "month", date.today().strftime("%Y-%m")
    )

    try:
        report_month = date.fromisoformat(selected_month + "-01")
        selected_month = report_month.strftime("%Y-%m")
    except ValueError:
        report_month = date.today().replace(day=1)
        selected_month = report_month.strftime("%Y-%m")

    user_id = session["user_id"]
    connection = get_db_connection()

    if connection is None:
        flash("Database connection failed.")
        return render_template(
            "monthly_report.html",
            expenses=[],
            total_expenses=0,
            selected_month=selected_month,
        )

    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, title, amount, category, description, expense_date
            FROM expenses
            WHERE user_id = %s
              AND expense_date >= %s
              AND expense_date < DATE_ADD(%s, INTERVAL 1 MONTH)
            ORDER BY expense_date DESC, id DESC
            """,
            (user_id, report_month, report_month),
        )
        expenses = cursor.fetchall()

        cursor.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS total_expenses
            FROM expenses
            WHERE user_id = %s
              AND expense_date >= %s
              AND expense_date < DATE_ADD(%s, INTERVAL 1 MONTH)
            """,
            (user_id, report_month, report_month),
        )
        total_expenses = cursor.fetchone()["total_expenses"]

        return render_template(
            "monthly_report.html",
            expenses=expenses,
            total_expenses=total_expenses,
            selected_month=selected_month,
        )

    except Exception:
        app.logger.exception("Monthly report failed.")
        flash("Could not load the monthly report.")

        return render_template(
            "monthly_report.html",
            expenses=[],
            total_expenses=0,
            selected_month=selected_month,
        )

    finally:
        if cursor is not None:
            cursor.close()
        connection.close()


# --------------------------------------------------
# RUN APPLICATION
# --------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)