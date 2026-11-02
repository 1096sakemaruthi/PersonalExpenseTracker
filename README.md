# Personal Expense Tracker

A web-based Personal Expense Tracker developed using Python, Flask, HTML, CSS, and MySQL. This application helps users manage their income and expenses, track transactions, monitor their balance, and view monthly expense reports.

## Features

- **User Registration:** Create a new account.
- **User Login:** Log in securely to access the application.
- **User Logout:** Securely log out from the application.
- **Dashboard:** View total income, total expenses, and total balance.
- **Add Expense:** Record new expenses with relevant details.
- **Edit Expense:** Update existing expense records.
- **Delete Expense:** Remove expense records.
- **Add Income:** Record income details.
- **Income History:** View recorded income transactions.
- **Edit Income:** Update existing income records.
- **Delete Income:** Remove income records.
- **Monthly Report:** View monthly expense reports.
- **Transaction Management:** Manage personal income and expense records.

## Technologies Used

- Python
- Flask
- HTML
- CSS
- MySQL
- MySQL Workbench

## Project Structure

```text
PersonalExpenseTracker/
│
├── app.py
├── db.py
├── requirements.txt
├── README.md
├── .env.example
├── .gitignore
│
├── static/
│   ├── style.css
│   ├── auth.css
│   ├── add_expense.css
│   ├── add_income.css
│   ├── edit_expense.css
│   ├── edit_income.css
│   ├── income_list.css
│   └── monthly_report.css
│
└── templates/
    ├── index.html
    ├── login.html
    ├── register.html
    ├── add_expense.html
    ├── add_income.html
    ├── edit_expense.html
    ├── edit_income.html
    ├── income_list.html
    └── monthly_report.html
```

## Requirements

Make sure the following software is installed:

- Python
- MySQL Server
- MySQL Workbench

## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/1096sakemaruthi/PersonalExpenseTracker.git
```

### 2. Navigate to the Project Folder

```bash
cd PersonalExpenseTracker
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
```

### 4. Activate the Virtual Environment

For Windows:

```bash
venv\Scripts\activate
```

### 5. Install Required Packages

```bash
pip install -r requirements.txt
```

### 6. Configure Environment Variables

Create a `.env` file in the project root directory using `.env.example` as a reference.

Add your own MySQL connection details:

```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=personal_expense_tracker
FLASK_SECRET_KEY=your_random_secret_key
```

Replace the example values with your actual database credentials and a secure secret key.

**Important:** Never upload your `.env` file or share your database password publicly.

### 7. Configure the MySQL Database

- Open MySQL Workbench.
- Connect to your MySQL Server.
- Make sure the `personal_expense_tracker` database is available.
- Make sure the required `expenses` and `income` tables are created with the columns used by the application.

## Run the Application

### 1. Check MySQL Database Connection

```bash
python db.py
```

If the connection is successful, the following message will appear:

```text
MySQL database connected successfully!
```

### 2. Start the Flask Application

```bash
python app.py
```

### 3. Open the Application

Open your web browser and visit:

```text
http://127.0.0.1:5000
```

Keep the Command Prompt running while using the application.

To stop the Flask server, press `Ctrl + C`.

## Security Notes

- Keep your `.env` file private.
- Never upload database passwords or secret keys to GitHub.
- The `.gitignore` file excludes `.env`, virtual environment folders, and Python cache files.
- Use `.env.example` as a reference for environment configuration.
- This project is intended for local learning and development.

## Author

**Maruthi**

GitHub: [1096sakemaruthi](https://github.com/1096sakemaruthi)

## Repository

[Personal Expense Tracker - GitHub](https://github.com/1096sakemaruthi/PersonalExpenseTracker)