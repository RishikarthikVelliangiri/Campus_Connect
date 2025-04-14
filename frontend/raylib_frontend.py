import raylib
import requests
from raylib import (InitWindow, SetTargetFPS, WindowShouldClose, BeginDrawing, 
                    EndDrawing, ClearBackground, GetMousePosition, IsMouseButtonReleased, 
                    DrawRectangle, DrawText, MeasureText, CloseWindow)
import time
import json

# --- Global Configuration ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Define colors (using Raylib color constants)
BG_COLOR = raylib.DARKBLUE
BUTTON_COLOR = raylib.LIGHTGRAY
BUTTON_HOVER = raylib.GRAY
TEXT_COLOR = raylib.WHITE

# Global variable for current screen state
# States: "welcome", "login", "register", "dashboard"
current_screen = "welcome"

# Optionally, store user info after login/registration
user_info = None

# --- Utility: Draw a Button and return True if clicked ---
def draw_button(x, y, width, height, text, 
                base_color=BUTTON_COLOR, hover_color=BUTTON_HOVER, text_color=TEXT_COLOR):
    mouse_pos = GetMousePosition()
    hovered = (x <= mouse_pos.x <= x + width and y <= mouse_pos.y <= y + height)
    current_color = hover_color if hovered else base_color
    DrawRectangle(x, y, width, height, current_color)
    # Center the text on the button
    text_width = MeasureText(text.encode(), 20)
    DrawText(text.encode(), x + (width - text_width) // 2, y + (height - 20) // 2, 20, text_color)
    if hovered and IsMouseButtonReleased(raylib.MOUSE_BUTTON_LEFT):
        return True
    return False

# --- Screen Functions ---

def welcome_screen():
    global current_screen
    # Draw title and navigation buttons
    DrawText(b"CampusCafe Connect", SCREEN_WIDTH//2 - 200, 50, 40, TEXT_COLOR)
    
    if draw_button(300, 150, 200, 50, "Login"):
        current_screen = "login"
    if draw_button(300, 220, 200, 50, "Register"):
        current_screen = "register"
    if draw_button(300, 290, 200, 50, "Dashboard"):
        current_screen = "dashboard"

def login_screen():
    global current_screen, user_info
    DrawText(b"Login", SCREEN_WIDTH//2 - 50, 50, 40, TEXT_COLOR)
    
    # For simplicity, we simulate text fields as variables.
    # In a real application you might use an on-screen keyboard input routine.
    # Here we just display prompt texts.
    DrawText(b"Press L to login (simulate sending credentials)", 150, 150, 20, TEXT_COLOR)
    DrawText(b"Press B to go back", 150, 180, 20, TEXT_COLOR)
    
    # Simulate button presses via key events for demo purposes
    if raylib.IsKeyPressed(raylib.KEY_L):
        # In a real app, you'd collect input values.
        # For this demo, we simulate a login by sending a fixed request.
        payload = {"username": "demo", "password": "demo"}
        try:
            resp = requests.post("http://127.0.0.1:5000/login", json=payload)
            data = resp.json()
            if "error" not in data:
                user_info = data.get("user")
                current_screen = "dashboard"
            else:
                print("Login error:", data["error"])
        except Exception as e:
            print("Login request failed:", e)
            
    if raylib.IsKeyPressed(raylib.KEY_B):
        current_screen = "welcome"

def register_screen():
    global current_screen, user_info
    DrawText(b"Register", SCREEN_WIDTH//2 - 60, 50, 40, TEXT_COLOR)
    DrawText(b"Press R to register (simulate new user)", 150, 150, 20, TEXT_COLOR)
    DrawText(b"Press B to go back", 150, 180, 20, TEXT_COLOR)
    
    if raylib.IsKeyPressed(raylib.KEY_R):
        # Simulate registration with fixed data
        payload = {"username": "newuser", "password": "newpass", "dorm": "West", "room": "101"}
        try:
            resp = requests.post("http://127.0.0.1:5000/register", json=payload)
            data = resp.json()
            if "error" not in data:
                print("Registration successful")
                current_screen = "login"
            else:
                print("Registration error:", data["error"])
        except Exception as e:
            print("Registration request failed:", e)
    if raylib.IsKeyPressed(raylib.KEY_B):
        current_screen = "welcome"

def dashboard_screen():
    global current_screen, user_info
    DrawText(b"Dashboard", SCREEN_WIDTH//2 - 70, 50, 40, TEXT_COLOR)
    if user_info:
        user_display = f"User: {user_info.get('username')} | Dorm: {user_info.get('dorm')} | Room: {user_info.get('room')}"
    else:
        user_display = "Not logged in"
    DrawText(user_display.encode(), 100, 120, 20, TEXT_COLOR)
    
    # Buttons to simulate navigation to different functionality pages.
    if draw_button(300, 200, 200, 50, "Order Food"):
        # For this demo, we simulate an order process
        # In practice this would go to an order page where menu is displayed.
        simulate_order()
    if draw_button(300, 270, 200, 50, "Logout"):
        user_info = None
        current_screen = "welcome"

    if draw_button(10, SCREEN_HEIGHT - 40, 150, 30, "Back"):
        current_screen = "welcome"

def simulate_order():
    # For demo purposes, simulate placing an order with fixed values.
    payload = {
        "username": user_info.get("username") if user_info else "unknown",
        "cafe": "Hashtag",
        "items": [
            {"item": "Pizza", "price": 200, "quantity": 1},
            {"item": "Soda", "price": 50, "quantity": 2}
        ]
    }
    try:
        resp = requests.post("http://127.0.0.1:5000/order", json=payload)
        data = resp.json()
        print("Order Response:", data)
    except Exception as e:
        print("Order request failed:", e)

def render_current_screen():
    # Clear the background
    ClearBackground(BG_COLOR)
    if current_screen == "welcome":
        welcome_screen()
    elif current_screen == "login":
        login_screen()
    elif current_screen == "register":
        register_screen()
    elif current_screen == "dashboard":
        dashboard_screen()
    # Add additional screens as needed

# --- Main Application Loop ---
def main():
    InitWindow(SCREEN_WIDTH, SCREEN_HEIGHT, b"CampusCafe Connect")
    SetTargetFPS(FPS)
    
    while not WindowShouldClose():
        BeginDrawing()
        render_current_screen()
        EndDrawing()
        
    CloseWindow()

if __name__ == "__main__":
    main()
