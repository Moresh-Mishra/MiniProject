import mysql.connector
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def init_database():
    # Connect to MySQL server
    conn = mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )
    
    cursor = conn.cursor()
    
    # Create database if it doesn't exist
    # cursor.execute(f"CREATE DATABASE IF NOT EXISTS {os.getenv('DB_NAME')}")
    
    # Use the database
    cursor.execute(f"USE {os.getenv('DB_NAME')}")
    
    # Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user (
            id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(120) UNIQUE NOT NULL,
            password_hash VARCHAR(128),
            first_name VARCHAR(50),
            last_name VARCHAR(50)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS account (
            id INT AUTO_INCREMENT PRIMARY KEY,
            account_number VARCHAR(20) UNIQUE NOT NULL,
            account_type VARCHAR(20) NOT NULL,
            balance FLOAT DEFAULT 0.0,
            user_id INT,
            FOREIGN KEY (user_id) REFERENCES user(id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transaction (
            id INT AUTO_INCREMENT PRIMARY KEY,
            amount FLOAT NOT NULL,
            transaction_type VARCHAR(20) NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            description VARCHAR(200),
            account_id INT,
            FOREIGN KEY (account_id) REFERENCES account(id)
        )
    """)
    
    # Commit changes and close connection
    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    init_database()
    print("Database initialized successfully!") 