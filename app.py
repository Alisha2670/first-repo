from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, session
import os
import json
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import sqlite3

# Load environment variables from .env file
load_dotenv()

# Initialize the Flask app
app = Flask(__name__)

# Set up SQLite database URI and secret key from environment variables
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("SQLALCHEMY_DATABASE_URI", "sqlite:///app.db")  # SQLite default path
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = os.environ.get("SECRET_KEY","default_secret_key")

# Initialize the database
db = SQLAlchemy(app)

# Define User and CartItem models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    cart = db.relationship("CartItem", backref="user", lazy=True)

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Ensure tables are created when the app starts
#with app.app_context():
 #   db.create_all()
with app.app_context():
    if not os.path.exists("app.db"):  # Prevents overwriting existing DB
        db.create_all()


# Home route
@app.route("/")
def index():
    existing_user = None
    if session.get("logged_in"):
        email = session.get("email")
        existing_user = User.query.filter_by(email=email).first()
    return render_template("index.html", existing_user=existing_user)

# About route
@app.route("/about")
def about():
    return render_template("about.html")

# Contact route
@app.route("/contact")
def contact():
    return render_template("contact.html")

# Shop route (static JSON file could be used here)
@app.route("/shop")
def shop():
    data = []
    with open("data/products.json", "r") as json_data:
        data = json.load(json_data)
    return render_template("shop.html", company=data)

# Login route
@app.route("/login", methods=["POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        existing_user = User.query.filter_by(email=email).first()
        if existing_user and check_password_hash(existing_user.password, password):
            flash("Login successful", "success")
            session["logged_in"] = True
            session["email"] = email
            return redirect(url_for("profile"))
        else:
            flash("Invalid email or password", "error")

    session["logged_in"] = False
    return redirect(url_for("index"))

# Checkout route
@app.route("/checkout", methods=["POST"])
def checkout():
    if request.method == "POST":
        cart_items = request.json.get("cartItems", [])
        user_email = session.get("email")

        if user_email:
            update_user_cart(user_email, cart_items)
            return jsonify({"message": "Checkout successful"})

    return jsonify({"error": "Invalid request"})

# Profile route
@app.route("/profile", methods=["GET", "POST"])
def profile():
    if request.method == "POST":
        if request.form.get("delete_profile"):
            delete_user()
            return redirect(url_for("index"))
        elif request.form.get("update_profile"):
            update_user_information()
            session.clear()
            return redirect(url_for("index"))

    user_email = session.get("email")
    user_data = User.query.filter_by(email=user_email).first()
    cart_items_from_db = CartItem.query.filter_by(user_id=user_data.id).all()
    return render_template("profile.html", user_data=user_data, cart_items_from_db=cart_items_from_db)

# Update user information
def update_user_information():
    new_username = request.form.get("username")
    new_email = request.form.get("emailprofile")
    new_password = request.form.get("passwordprofile")

    user_email = session.get("email")
    user_data = User.query.filter_by(email=user_email).first()

    if new_username:
        user_data.username = new_username
    if new_email:
        user_data.email = new_email
    if new_password:
        hashed_password = generate_password_hash(new_password, method="pbkdf2:sha256")
        user_data.password = hashed_password

    db.session.commit()

# Update user cart
def update_user_cart(email, cart_items):
    user = User.query.filter_by(email=email).first()
    if user:
        # Clear existing cart and add new items
    
        for item in cart_items:
            new_cart_item = CartItem(name=item["name"], quantity=item["quantity"], user_id=user.id)
            db.session.add(new_cart_item)
        db.session.commit()

# Remove item from cart
def remove_item_from_cart(email, item_to_remove):
    user = User.query.filter_by(email=email).first()
    if user:
        cart_item = CartItem.query.filter_by(user_id=user.id, name=item_to_remove["name"]).first()
        if cart_item:
            db.session.delete(cart_item)
            db.session.commit()

# Delete user account
def delete_user():
    user_email = session.get("email")
    user_data = User.query.filter_by(email=user_email).first()
    db.session.delete(user_data)
    db.session.commit()
    session.clear()

# Signup route
@app.route("/signup", methods=["GET", "POST"])
def signup():
    username_exists = False
    success_exists = session.pop("success_exists", False)

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        email = request.form.get("email")

        try:
            existing_user = User.query.filter_by(username=username).first()

            if existing_user:
                flash("Username already exists", "error")
                username_exists = True
                return render_template("signup.html", username_exists=username_exists)

            elif password != confirm_password:
                flash("Passwords do not match", "error")
                return render_template("signup.html", username_exists=username_exists)

            hashed_password = generate_password_hash(password, method="pbkdf2:sha256")

            new_user = User(username=username, email=email, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()

            session["success_exists"] = True
            return redirect(url_for("signup"))

        except Exception as e:
            print(f"Error accessing or inserting user into SQLite: {e}")
            flash("Error accessing or inserting user into SQLite", "error")
            return render_template("signup.html", username_exists=username_exists)

    return render_template("signup.html", username_exists=username_exists, success_exists=success_exists)

# API route for products (this can be static or from a database)
@app.route("/api/products")
def products():
    products_data = [...]  # Add your product data here
    return jsonify(products_data)

# Logout route
@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("Logout successful", "success")
    return redirect(url_for("index"))

# Update quantity route
@app.route("/update_quantity", methods=["POST"])
def update_quantity():
    if request.method == "POST":
        data = request.get_json()
        item_name = data.get("itemName")
        new_quantity = int(data.get("updatedQuantity"))

        user_email = session.get("email")
        update_quantity_in_cart(user_email, item_name, new_quantity)

        return jsonify({"message": "Quantity updated successfully"})

    return jsonify({"error": "Invalid request"})

# Update item quantity in cart
def update_quantity_in_cart(email, item_name, new_quantity):
    user = User.query.filter_by(email=email).first()
    cart_item = CartItem.query.filter_by(user_id=user.id, name=item_name).first()
    if cart_item:
        cart_item.quantity = new_quantity
        db.session.commit()

# Running the Flask app
if __name__ == "__main__":
    app.run(host=os.environ.get("IP", "127.0.0.1"), port=int(os.environ.get("PORT", 5000)), debug=True)


