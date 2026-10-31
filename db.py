import os

import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# Load database settings from the local .env file.
load_dotenv()


def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "personal_expense_tracker"),
        )

        if connection.is_connected():
            return connection

    except (Error, ValueError) as error:
        print("Database connection error:", error)

    return None


if __name__ == "__main__":
    connection = get_db_connection()

    if connection:
        print("MySQL database connected successfully!")
        connection.close()
    else:
        print("MySQL database connection failed.")
