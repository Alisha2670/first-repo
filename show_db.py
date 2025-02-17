import sqlite3

# Connect to the database
conn = sqlite3.connect("app.db")
cursor = conn.cursor()

# Fetch and display all users
print("\n📌 Users Table:")
cursor.execute("SELECT id, username, email, password FROM users")  # Fetch all users
users = cursor.fetchall()

if users:
    print("ID | Username | Email | Password Hash")
    print("-" * 50)
    for user in users:
        print(user)
else:
    print("No users found in the database.")

# Fetch and display all cart items
print("\n🛒 Cart Items Table:")
cursor.execute("SELECT id, user_id, name, quantity FROM cart_items")  # Fetch all cart items
cart_items = cursor.fetchall()

if cart_items:
    print("ID | User ID | Product Name | Quantity")
    print("-" * 50)
    for item in cart_items:
        print(item)
else:
    print("No cart items found in the database.")

# Close the connection
conn.close()
