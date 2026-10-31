# Personal Expense Tracker

A beginner-friendly web application to manage personal income and expenses using Python, Flask, HTML, CSS, and MySQL.

## Features

- Dashboard displaying total income, total expenses, and balance.
- Add income records.
- Add, edit, and delete expense records.
- View recent transactions.
- View monthly expense reports.
- Form validation for required fields and positive amounts.

## Technologies Used

- Python
- Flask
- HTML and CSS
- MySQL
- MySQL Workbench

## Project Structure

```text
PersonalExpenseTracker/
├── app.py
├── db.py
├── requirements.txt
├── README.md
├── .env
├── .env.example
├── .gitignore
├── templates/
│   ├── index.html
│   ├── add_expense.html
│   ├── add_income.html
│   ├── edit_expense.html
│   └── monthly_report.html
└── static/
    ├── style.css
    ├── add_expense.css
    ├── add_income.css
    └── monthly_report.css
```

## Requirements

- Python installed
- MySQL Server running
- MySQL Workbench for database management
- Database credentials configured in `.env`

## Setup Instructions

1. Open MySQL Workbench and connect to your MySQL server.
2. Make sure the `personal_expense_tracker` database and the required `expenses` and `income` tables exist.
3. Create a `.env` file in the project root using `.env.example` as a template.
4. Enter your own MySQL connection details in `.env`. Never share this file publicly.
5. Open Command Prompt in the project folder.
6. Create and activate a virtual environment if needed:

   ```bat
   python -m venv venv
   venv\Scripts\activate
   ```

7. Install the dependencies:

   ```bat
   pip install -r requirements.txt
   ```

## Run the Application

Run these commands from the project folder with the virtual environment activated:

```bat
python db.py
python app.py
```

If the database connection succeeds, start the application and open:

http://127.0.0.1:5000

Keep the terminal running while using the application. Press `Ctrl+C` to stop the development server.

## Validation Checks

Test the Add Expense and Add Income forms:

- Empty required fields should be rejected.
- Negative amounts should be rejected.
- Zero amounts should be rejected.
- Valid positive amounts should save successfully.

## Database Verification

Run these queries in MySQL Workbench:

```sql
SELECT *
FROM personal_expense_tracker.expenses
ORDER BY expense_date DESC, id DESC;

SELECT *
FROM personal_expense_tracker.income
ORDER BY income_date DESC, id DESC;
```

## Security Notes

- Keep `.env` private.
- Do not share database passwords in public repositories or project files.
- `.gitignore` excludes `.env`, virtual environment folders, and Python cache files from Git.
- Do not delete your local `venv` folder while using the project.
- This project is intended for local learning and development.
