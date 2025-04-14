from flask import Flask, request, jsonify, send_from_directory, render_template
import json, os
from datetime import datetime, timedelta

app = Flask(__name__, 
            template_folder="../frontend/templates", 
            static_folder="../frontend/static")

# Data directory and file paths
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
ORDERS_FILE = os.path.join(DATA_DIR, "orders.json")

# Ensure data directory exists
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def load_data(filename):
    if not os.path.exists(filename):
        return {}
    with open(filename, "r") as f:
        return json.load(f)

def save_data(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

# Initialize files with empty structures if needed
if not os.path.exists(USERS_FILE):
    save_data(USERS_FILE, {"users": []})
if not os.path.exists(ORDERS_FILE):
    save_data(ORDERS_FILE, {"orders": []})

# Hard-coded menu for the four campus cafes
MENUS = {
    "Hashtag": [
        {"item": "Aloo tikki burger", "price": 90},
        {"item": "Fries", "price": 100},
        {"item": "Soda", "price": 50},
        {"item": "Pizza", "price": 200}
    ],
    "Korebi": [
        {"item": "Espresso tonic", "price": 130},
        {"item": "Espresso", "price": 100},
        {"item": "Vietnamese Coffee", "price": 200},
        {"item": "Green tea", "price": 60}
    ],
    "Charlie's Cafe": [
        {"item": "Falafel Shawrma", "price": 100},
        {"item": "Paneer Sandwich", "price": 80},
        {"item": "Cold coffee", "price": 60},
        {"item": "Salad", "price": 60}
    ],
    "Blue Tokai": [
        {"item": "Croissant", "price": 50},
        {"item": "Espresso", "price": 100},
        {"item": "Iced Tea", "price": 150},
        {"item": "Muffin", "price": 130}
    ]
}

# --------------------
# Web page routes
# --------------------

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/login_page")
def login_page():
    return render_template("login.html")

@app.route("/register_page")
def register_page():
    return render_template("register.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/order_page")
def order_page():
    return render_template("order.html")

@app.route("/order_status_page")
def order_status_page():
    return render_template("order_status.html")

# --------------------
# API endpoints
# --------------------

@app.route("/menu", methods=["GET"])
def get_menu():
    return jsonify(MENUS)

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    region = data.get("region")
    letter = data.get("letter")
    if not username or not password or not region or not letter:
        return jsonify({"error": "Missing fields"}), 400
    # Combine region and letter (e.g. "West A")
    dorm = f"{region} {letter}"
    users_data = load_data(USERS_FILE)
    for user in users_data["users"]:
        if user["username"] == username:
            return jsonify({"error": "Username already exists"}), 400
    new_user = {"username": username, "password": password, "dorm": dorm}
    users_data["users"].append(new_user)
    save_data(USERS_FILE, users_data)
    return jsonify({"message": "Registration successful"})

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    users_data = load_data(USERS_FILE)
    for user in users_data["users"]:
        if user["username"] == username and user["password"] == password:
            return jsonify({"message": "Login successful", "user": user})
    return jsonify({"error": "Invalid credentials"}), 401

@app.route("/order", methods=["POST"])
def order():
    data = request.get_json()
    username = data.get("username")
    cafe = data.get("cafe")
    items = data.get("items")
    if not username or not cafe or not items:
        return jsonify({"error": "Missing order details"}), 400
    orders_data = load_data(ORDERS_FILE)
    # Create a unique order_id based on count (in production use proper UID)
    order_id = len(orders_data.get("orders", [])) + 1
    order_record = {
        "order_id": order_id,
        "username": username,
        "cafe": cafe,
        "items": items,
        "timestamp": datetime.now().isoformat(),
        "status": "Delivering"  # start with 'Delivering'
    }
    orders_data["orders"].append(order_record)
    save_data(ORDERS_FILE, orders_data)
    return jsonify({"message": "Order placed successfully", "order": order_record})

@app.route("/order_status/<int:order_id>", methods=["GET"])
def order_status(order_id):
    orders_data = load_data(ORDERS_FILE)
    # Use a generator expression that only considers orders with 'order_id'
    order = next((o for o in orders_data.get("orders", []) if o.get("order_id") == order_id), None)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    # Check if 1 minute has passed since timestamp
    order_time = datetime.fromisoformat(order["timestamp"])
    if order["status"] == "Delivering" and datetime.now() - order_time >= timedelta(minutes=1):
        order["status"] = "Order Delivered"
        save_data(ORDERS_FILE, orders_data)
    return jsonify({"order": order})

if __name__ == "__main__":
    app.run(debug=True)
