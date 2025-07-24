import os
import json
import hashlib
import re
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.toast import toast
from kivy.metrics import dp

USERS_JSON_PATH = os.path.join("data", "registered_user", "users.json")
MATCH_BASE_DIR = os.path.join("data", "matches_history")

class RegisterScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = MDBoxLayout(
            orientation='vertical',
            padding=dp(40),
            spacing=dp(20),
            adaptive_height=True,
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )

        title = MDLabel(
            text="Register",
            halign="center",
            font_style="H4"
        )

        self.username_field = MDTextField(
            hint_text="Username",
            icon_right="account"
        )

        self.email_field = MDTextField(
            hint_text="Email",
            icon_right="email"
        )

        self.password_field = MDTextField(
            hint_text="Password",
            password=True,
            icon_right="key-variant"
        )

        register_button = MDRaisedButton(
            text="REGISTER",
            on_release=self.register,
            pos_hint={'center_x': 0.5}
        )

        login_button = MDFlatButton(
            text="Already have an account? Login",
            on_release=self.go_to_login,
            pos_hint={'center_x': 0.5}
        )

        layout.add_widget(title)
        layout.add_widget(self.username_field)
        layout.add_widget(self.email_field)
        layout.add_widget(self.password_field)
        layout.add_widget(register_button)
        layout.add_widget(login_button)

        self.add_widget(layout)

        # Ensure data directories exist
        os.makedirs(os.path.dirname(USERS_JSON_PATH), exist_ok=True)
        os.makedirs(MATCH_BASE_DIR, exist_ok=True)

    def is_valid_email(self, email):
        return re.match(r"[^@]+@[^@]+\.[^@]+", email)

    def is_valid_password(self, password):
        return len(password) >= 6

    def load_users(self):
        if os.path.exists(USERS_JSON_PATH):
            with open(USERS_JSON_PATH, "r") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return []
        return []

    def save_users(self, users):
        with open(USERS_JSON_PATH, "w") as f:
            json.dump(users, f, indent=4)

    def is_username_taken(self, username, users):
        return any(user["username"] == username for user in users)

    def clear_fields(self):
        self.username_field.text = ""
        self.email_field.text = ""
        self.password_field.text = ""

    def register(self, instance):
        username = self.username_field.text.strip().lower()
        email = self.email_field.text.strip()
        password = self.password_field.text.strip()

        if not username or not email or not password:
            toast("Please fill all fields")
            return

        if not self.is_valid_email(email):
            toast("Invalid email format")
            return

        if not self.is_valid_password(password):
            toast("Password must be at least 6 characters")
            return

        users = self.load_users()

        if self.is_username_taken(username, users):
            toast("Username already exists!")
            return

        try:
            # Create match history folder for this user
            os.makedirs(os.path.join(MATCH_BASE_DIR, username), exist_ok=True)

            hashed_password = hashlib.sha256(password.encode()).hexdigest()

            new_user = {
                "username": username,
                "email": email,
                "password": hashed_password
            }

            users.append(new_user)
            self.save_users(users)

            toast(f"User {username} registered!")
            self.clear_fields()
            # Redirect to login page after registration
            self.manager.current = "login"

        except Exception as e:
            toast(f"Registration failed: {str(e)}")

    def go_to_login(self, instance):
        self.manager.current = "login"
