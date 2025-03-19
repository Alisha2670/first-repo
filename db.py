import sqlite3
import os

# Define the path to your database
db_path = 'app.db'

# Connect to the SQLite database (it will be created if it doesn't exist)
connection = sqlite3.connect(db_path)

# Create a cursor object to interact with the database
cursor = connection.cursor()

# Create the 'users' table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,w
        password TEXT NOT NULL,
        cart_items TEXT DEFAULT ''
    )
''')

# Create the 'cart_items' table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS cart_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL,
        imgSrc TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
''')

# Commit the changes and close the connection
connection.commit()

# Close the connection
connection.close()

print("Database and tables created successfully.")

