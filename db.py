
import os

import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# Load database settings from the .env file
load_dotenv()


def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT", "14748")),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME", "defaultdb"),

            # Aiven SSL settings
            ssl_ca=os.getenv("DB_SSL_CA"),
            ssl_verify_cert=True
        )

        if connection.is_connected():
            return connection

    except (Error, ValueError) as error:
        print("Database connection error:", error)

    return None


if __name__ == "__main__":
    connection = get_db_connection()

    if connection:
        print("Aiven MySQL database connected successfully!")
        connection.close()
    else:
        print("Aiven MySQL database connection failed.")
