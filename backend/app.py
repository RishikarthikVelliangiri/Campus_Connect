# backend/app.py
from flask import Flask, request, jsonify, render_template, redirect, url_for
import json
import os
from datetime import datetime # Removed timedelta
from collections import Counter

app = Flask(__name__,
            template_folder="../frontend/templates",
            static_folder="../frontend/static")

# --- Data Handling (same as before) ---
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
ORDERS_FILE = os.path.join(DATA_DIR, "orders.json")

if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)

def load_data(filename):
    default_structure = {"users": []} if 'users' in filename else {"orders": []}
    if not os.path.exists(filename): return default_structure
    try:
        with open(filename, "r") as f: content = f.read().strip()
        if not content: return default_structure
        return json.loads(content)
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return default_structure

def save_data(filename, data):
    try:
        with open(filename, "w") as f: json.dump(data, f, indent=4)
    except Exception as e: print(f"Error saving data to {filename}: {e}")

if not os.path.exists(USERS_FILE): save_data(USERS_FILE, {"users": []})
if not os.path.exists(ORDERS_FILE): save_data(ORDERS_FILE, {"orders": []})

# --- Menus (same as before) ---
MENUS = {
    "Hashtag": [{"item": "Aloo tikki burger", "price": 90}, {"item": "Fries", "price": 100}, {"item": "Soda", "price": 50}, {"item": "Pizza", "price": 200}],
    "Korebi": [{"item": "Espresso tonic", "price": 130}, {"item": "Espresso", "price": 100}, {"item": "Vietnamese Coffee", "price": 200}, {"item": "Green tea", "price": 60}],
    "Charlie's Cafe": [{"item": "Falafel Shawrma", "price": 100}, {"item": "Paneer Sandwich", "price": 80}, {"item": "Cold coffee", "price": 60}, {"item": "Salad", "price": 60}],
    "Blue Tokai": [{"item": "Croissant", "price": 50}, {"item": "Espresso", "price": 100}, {"item": "Iced Tea", "price": 150}, {"item": "Muffin", "price": 130}]
}

# --- Web Page Routes ---

@app.route("/")
def home(): return render_template("home.html")

@app.route("/login_page")
def login_page(): return render_template("login.html")

@app.route("/register_page")
def register_page(): return render_template("register.html")

@app.route("/dashboard") # User dashboard
def dashboard(): return render_template("dashboard.html")

@app.route("/order_page")
def order_page(): return render_template("order.html")

@app.route("/order_status_page")
def order_status_page(): return render_template("order_status.html")

@app.route("/admin_dashboard") # Super admin dashboard
def admin_dashboard(): return render_template("admin_dashboard.html")

# --- NEW: Cafe Admin Dashboard Route ---
@app.route("/cafe_admin_dashboard")
def cafe_admin_dashboard():
    # Client-side JS will handle redirect if not a cafe admin
    return render_template("cafe_admin_dashboard.html")


# --- API Endpoints ---

@app.route("/api/menu", methods=["GET"])
def api_get_menu(): return jsonify(MENUS)

@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json()
    print(f"[*] Register attempt: {data.get('username')}")
    username = data.get("username")
    password = data.get("password")
    region = data.get("region")
    letter = data.get("letter")

    # Basic validation
    if not all([username, password, region, letter]): return jsonify({"error": "Missing fields"}), 400
    if region not in ["West", "East", "South"] or not letter.isalpha() or len(letter) != 1: return jsonify({"error": "Invalid region/letter"}), 400
    # Prevent registering admin-like usernames
    if username.endswith('_admin') or username == 'admin': return jsonify({"error": "Invalid username"}), 400

    dorm = f"{region} {letter.upper()}"
    users_data = load_data(USERS_FILE)
    if "users" not in users_data: users_data["users"] = []

    if any(user["username"] == username for user in users_data["users"]): return jsonify({"error": "Username exists"}), 400

    new_user = {"username": username, "password": password, "dorm": dorm} # No cafe info for regular users
    users_data["users"].append(new_user)
    save_data(USERS_FILE, users_data)
    print(f"[+] User '{username}' registered.")
    return jsonify({"message": "Registration successful"}), 201

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    print(f"[*] Login attempt: {username}")

    if not username or not password: return jsonify({"error": "Missing credentials"}), 400

    users_data = load_data(USERS_FILE)
    user_found = next((user for user in users_data.get("users", []) if user["username"] == username), None)

    if user_found and user_found["password"] == password: # Plain text check
        # Prepare user info, include managed_cafe if it exists
        user_info = {
            "username": user_found["username"],
            "dorm": user_found.get("dorm", "N/A")
        }
        # --- ADDED: Include managed_cafe for cafe admins ---
        if "managed_cafe" in user_found:
            user_info["managed_cafe"] = user_found["managed_cafe"]
            print(f"[+] Cafe Admin Login successful: {username} for {user_info['managed_cafe']}")
        # --- Include role for super admin if needed ---
        elif "role" in user_found and user_found["role"] == "super_admin":
             user_info["role"] = "super_admin"
             print(f"[+] Super Admin Login successful: {username}")
        else:
            print(f"[+] User Login successful: {username}")

        return jsonify({"message": "Login successful", "user": user_info})
    else:
        print(f"[!] Login failed: {username}")
        return jsonify({"error": "Invalid username or password"}), 401

@app.route("/api/order", methods=["POST"])
def api_order():
    data = request.get_json()
    username = data.get("username")
    cafe = data.get("cafe")
    items = data.get("items")
    print(f"[*] Order received from '{username}' for '{cafe}'")

    if not username: return jsonify({"error": "Username missing"}), 400
    if not cafe or not items or not isinstance(items, list) or len(items) == 0: return jsonify({"error": "Missing order details"}), 400
    if cafe not in MENUS: return jsonify({"error": "Invalid cafe"}), 400

    orders_data = load_data(ORDERS_FILE)
    total_price = 0
    valid_items = []
    menu_for_cafe = MENUS.get(cafe, [])
    menu_lookup = {item["item"]: item["price"] for item in menu_for_cafe}

    for item_order in items:
        item_name, quantity = item_order.get("item"), item_order.get("quantity")
        if item_name in menu_lookup and isinstance(quantity, int) and quantity > 0:
            correct_price = menu_lookup[item_name]
            total_price += correct_price * quantity
            valid_items.append({"item": item_name, "price": correct_price, "quantity": quantity})
        else:
             print(f"[!] Invalid item in order: {item_name}")
             return jsonify({"error": f"Invalid item/quantity: {item_name}"}), 400

    if not valid_items: return jsonify({"error": "No valid items"}), 400

    if "orders" not in orders_data: orders_data["orders"] = []
    order_id = len(orders_data.get("orders", [])) + 1

    order_record = {
        "order_id": order_id, "username": username, "cafe": cafe,
        "items": valid_items, "total_price": total_price,
        "timestamp": datetime.now().isoformat(),
        # --- CHANGED: Initial status is always Pending ---
        "status": "Pending"
    }
    orders_data["orders"].append(order_record)
    save_data(ORDERS_FILE, orders_data)
    print(f"[+] Order #{order_id} placed (Status: Pending).")
    return jsonify({"message": "Order placed successfully", "order": order_record}), 201


@app.route("/api/order_status/<int:order_id>", methods=["GET"])
def api_order_status(order_id):
    # --- REMOVED: Automatic time-based status updates ---
    # This endpoint now simply returns the current status from the file.
    orders_data = load_data(ORDERS_FILE)
    order = next((o for o in orders_data.get("orders", []) if o.get("order_id") == order_id), None)

    if not order: return jsonify({"error": "Order not found"}), 404

    # print(f"[*] Status check for Order #{order_id}: Current status '{order.get('status')}'")
    return jsonify({"order": order})

@app.route("/api/my_orders", methods=["GET"]) # For regular user dashboard
def api_my_orders():
    username = request.args.get('username')
    if not username: return jsonify({"error": "Username required"}), 400

    orders_data = load_data(ORDERS_FILE)
    user_orders = [o for o in orders_data.get("orders", []) if o.get("username") == username]
    user_orders.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    return jsonify({"orders": user_orders})

@app.route("/api/admin/summary", methods=["GET"]) # For super admin dashboard
def api_admin_summary():
    # Add proper auth check in real app
    orders_data = load_data(ORDERS_FILE)
    all_orders = orders_data.get("orders", [])
    cafe_counts = Counter(order['cafe'] for order in all_orders if 'cafe' in order)
    total_revenue = sum(order.get('total_price', 0) for order in all_orders)
    all_orders.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    recent_orders = all_orders[:5]
    summary = {
        "orders_per_cafe": dict(cafe_counts), "total_revenue": round(total_revenue, 2),
        "recent_orders": recent_orders
    }
    return jsonify(summary)

# --- NEW: Cafe Admin API Endpoints ---

@app.route("/api/cafe_admin/orders", methods=["GET"])
def api_cafe_admin_orders():
    # In a real app, verify the logged-in user *is* the admin for this cafe
    cafe_name = request.args.get('cafe')
    if not cafe_name:
        return jsonify({"error": "Cafe name parameter required"}), 400
    if cafe_name not in MENUS:
        return jsonify({"error": "Invalid cafe name"}), 400

    print(f"[*] Fetching orders for Cafe Admin: {cafe_name}")
    orders_data = load_data(ORDERS_FILE)
    # Get orders for this cafe, prioritize "Pending"
    cafe_orders = [o for o in orders_data.get("orders", []) if o.get("cafe") == cafe_name]
    # Sort: Pending first, then by time (newest first)
    cafe_orders.sort(key=lambda x: (x.get('status', '') != 'Pending', x.get('timestamp', '')), reverse=True)

    return jsonify({"orders": cafe_orders})

@app.route("/api/cafe_admin/mark_delivered/<int:order_id>", methods=["POST"])
def api_cafe_admin_mark_delivered(order_id):
    # In a real app, verify the logged-in user can manage the cafe for this order_id
    print(f"[*] Attempting to mark Order #{order_id} as delivered.")
    orders_data = load_data(ORDERS_FILE)
    order_found = False
    for order in orders_data.get("orders", []):
        if order.get("order_id") == order_id:
            if order.get("status") == "Pending": # Only mark pending orders as delivered
                order["status"] = "Order Delivered"
                save_data(ORDERS_FILE, orders_data)
                order_found = True
                print(f"[+] Order #{order_id} marked as delivered.")
                return jsonify({"message": f"Order {order_id} marked as delivered."})
            elif order.get("status") == "Order Delivered":
                 print(f"[!] Order #{order_id} already delivered.")
                 return jsonify({"error": f"Order {order_id} is already delivered."}), 400 # Bad Request
            else:
                 print(f"[!] Cannot mark Order #{order_id} with status '{order.get('status')}' as delivered.")
                 return jsonify({"error": f"Cannot update status for order {order_id}."}), 400

    if not order_found:
        print(f"[!] Order #{order_id} not found for delivery update.")
        return jsonify({"error": "Order not found"}), 404

    # Fallback generic error if something unexpected happens
    return jsonify({"error": "Failed to update order status"}), 500


# --- Main Execution ---
if __name__ == "__main__":
    print("[*] Starting Flask server...")
    app.run(host='0.0.0.0', port=5000, debug=True)
    print(f"[*] Server accessible on http://<your-local-ip>:5000")
    print(f"[*] Or locally via http://127.0.0.1:5000")