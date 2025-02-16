from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, session
import os
import json
from bson import ObjectId 
import secrets
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash

# Load environment variables from .env file if it exists
if os.path.exists("env.py"):
    import venv

app = Flask(__name__)

# Set MongoDB database name, URI, and secret key from environment variables
app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME", "your_default_db_name")  # Default value if not set
app.config["MONGO_URI"] = os.environ.get("MONGO_URI", "mongodb://localhost:27017/yourdatabase")  # Default URI
app.secret_key = os.environ.get("SECRET_KEY", "your_default_secret_key")  # Default secret key

try:
    mongo = PyMongo(app)
    print("Connected to MongoDB")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")

@app.route("/")
def index():
    """
    Render the index.html template with the existing user data 
    if the user is logged in.
    """
    existing_user = None
    if session.get("logged_in"):
        email = session.get("email")
        existing_user = mongo.db.users.find_one({"email": email})
    return render_template("index.html", existing_user=existing_user)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/shop")
def shop():
    """
    Render the shop.html template with the company data from the products.json file.
    """
    data = []
    with open("data/products.json", "r") as json_data:
        data = json.load(json_data)
    return render_template("shop.html", company=data)

@app.route("/login", methods=["POST"])
def login():
    """
    Handle user login by checking the provided email and password.
    If the login is successful, set the 'logged_in' session variable 
    to True and store the email in the session.
    Redirect the user to the profile page.
    """
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        existing_user = mongo.db.users.find_one({"email": email})
        if existing_user and check_password_hash(existing_user["password"], password):
            flash("Login successful", "success")
            # Set the 'logged_in' session variable to True
            session["logged_in"] = True
            session["email"] = email  # Optionally store the email in the session
            return redirect(url_for("profile"))
        else:
            flash("Invalid email or password", "error")

    # Set the 'logged_in' session variable to False if login is not successful
    session["logged_in"] = False
    return redirect(url_for("index"))

@app.route("/checkout", methods=["POST"])
def checkout():
    """
    Handle user checkout by updating the user's cart in the database 
    with the new cart items.
    """
    if request.method == "POST":
        cart_items = request.json.get("cartItems", [])

        user_email = session.get("email")

        # Update the user's cart in the database with the new cart items
        if user_email:
            update_user_cart(user_email, cart_items)
            return jsonify({"message": "Checkout successful"})

    return jsonify({"error": "Invalid request"})

@app.route("/profile", methods=["GET", "POST"])
def profile():
    """
    Handle user profile page requests.
    If the request method is POST, check for delete_profile 
    or update_profile flags and act accordingly.
    Render the profile.html template with the user data and cart items.
    """
    if request.method == "POST":
        if request.form.get("delete_profile"):
            # If delete_profile flag is present, delete the user
            delete_user()
            return redirect(url_for("index"))
        elif request.form.get("update_profile"):
            # Update user information
            update_user_information()
            session.clear()
            return redirect(url_for("index"))

    # Retrieve the actual user data from the MongoDB database
    user_email = session.get("email")
    user_data = mongo.db.users.find_one({"email": user_email})

    # Fetch cart items from the user's data
    cart_items_from_db = user_data.get("cart", [])

    return render_template("profile.html", user_data=user_data, 
                           cart_items_from_db=cart_items_from_db)

def update_user_information():
    # Get the updated information from the form
    new_username = request.form.get("username")
    new_email = request.form.get("emailprofile")
    new_password = request.form.get("passwordprofile")

    # Retrieve the actual user data from the MongoDB database
    user_email = session.get("email")
    user_data = mongo.db.users.find_one({"email": user_email})

    # Update the user's information if provided in the form
    if new_username:
        user_data["username"] = new_username
    if new_email:
        user_data["email"] = new_email
    if new_password:
        hashed_password = generate_password_hash(new_password, method="pbkdf2:sha256")
        user_data["password"] = hashed_password

    # Update the user in the database
    mongo.db.users.update_one({"email": user_email}, {"$set": user_data})

def update_user_cart(email , cart_items):
    """ 
    Assuming you have a 'users' collection in your MongoDB,
    Update the user's cart in the database.
    """
    user_collection = mongo.db.users

    # Find the user by email
    user  = user_collection.find_one({"email": email})
    if user:
        user_collection.update_one({"email": email}, {"$set": {"cart": cart_items}})

# # Delete Profile
def delete_user():
    # Assuming you have a 'users' collection in your MongoDB
    user_collection = mongo.db.users

    # Get the user's email from the session
    user_email = session.get("email")

    # Delete the user from the database
    user_collection.delete_one({"email": user_email})

    # Clear the session data
    session.clear()

@app.route("/remove_item", methods=["POST"])
def remove_item():
    if request.method == "POST":
        # Get the item details from the request
        item_to_remove = request.get_json().get("itemToRemove", {})

        user_email = session.get("email")

        # Update user cart in the database to remove the specified item
        if user_email:
            remove_item_from_cart(user_email, item_to_remove)
            return jsonify({"message": "Item removed successfully"})

    return jsonify({"error": "Invalid request"})

def remove_item_from_cart(email, item_to_remove):
    # Assuming you have a 'users' collection in your MongoDB
    user_collection = mongo.db.users

    # Update the user's cart in the database
    user_collection.update_one(
        {"email":email},
        {"$pull":{"cart":item_to_remove}}
    )

@app.route("/signup", methods=["GET", "POST"])
def signup():
    username_exists = False

    # Retrieve the success_exists variable from the session
    success_exists = session.pop("success_exists", False)

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        email = request.form.get("email")

        try:
            existing_user = mongo.db.users.find_one({"username": username})

            if existing_user:
                flash("Username already exists", "error")
                username_exists = True
                return render_template("signup.html", username_exists=username_exists)

            elif password != confirm_password:
                flash("Passwords do not match", "error")
                return render_template("signup.html", username_exists=username_exists)

            hashed_password = generate_password_hash(password, method="pbkdf2:sha256")

            mongo.db.users.insert_one({
                "username": username,
                "email": email,
                "password": hashed_password
            })

            # Set success_exists in the session
            session["success_exists"] = True
            return redirect(url_for("signup"))

        except Exception as e:
            print(f"Error accessing or inserting user into MongoDB: {e}")
            flash("Error accessing or inserting user into MongoDB", "error")
            return render_template("signup.html", username_exists=username_exists)

    return render_template("signup.html", username_exists=username_exists, 
                           success_exists=success_exists)

# Endpoint to provide Products data as JSON
@app.route("/api/products")
def products():
    products_data=[...]
    return jsonify(products_data)

@app.route("/logout", methods=["POST"])
def logout():
    # Clear the session data
    session.clear()
    flash("Logout successful", "success")
    return redirect(url_for("index"))

# Flask route for updating quantity
@app.route("/update_quantity", methods=["POST"])
def update_quantity():
    if request.method == "POST":
        data = request.get_json()
        item_name = data.get("itemName")  # Change the key to match the frontend
        new_quantity = int(data.get("updatedQuantity"))

        user_email = session.get("email")
        update_quantity_in_cart(user_email, item_name, new_quantity)

        return jsonify({"message": "Quantity updated successfully"})

    return jsonify({"error": "Invalid request"})

def update_quantity_in_cart(email, item_name, new_quantity):
    # Assuming you have a 'users' collection in your MongoDB
    user_collection = mongo.db.users

    # Update the user's cart in the database
    user_collection.update_one(
        {"email": email, "cart.name": item_name},
        {"$set": {"cart.$.quantity": new_quantity}}
    )


if __name__ == "__main__":
    # Set a default value for the IP and PORT if not specified in environment variables
    app.run(host=os.environ.get("IP", "127.0.0.1"),
            port=int(os.environ.get("PORT", 5000)),
            debug=True)
