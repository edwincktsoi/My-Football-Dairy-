import os
import json
import hashlib
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.toast import toast
from kivy.metrics import dp

USERS_JSON_PATH = os.path.join("data", "registered_user", "users.json")
MATCH_BASE_DIR = os.path.join("data", "matches_history")

class LoginScreen(MDScreen):
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
            text="Login",
            halign="center",
            font_style="H4"
        )

        self.email_field = MDTextField(
            hint_text="Email",
            helper_text="Enter your registered email",
            helper_text_mode="on_focus",
            icon_right="email"
        )

        self.password_field = MDTextField(
            hint_text="Password",
            password=True,
            icon_right="key-variant"
        )

        login_button = MDRaisedButton(
            text="LOGIN",
            on_release=self.login,
            pos_hint={'center_x': 0.5}
        )

        register_button = MDFlatButton(
            text="Don't have an account? Register",
            on_release=self.go_to_register,
            pos_hint={'center_x': 0.5}
        )

        layout.add_widget(title)
        layout.add_widget(self.email_field)
        layout.add_widget(self.password_field)
        layout.add_widget(login_button)
        layout.add_widget(register_button)

        self.add_widget(layout)

    def load_users(self):
        if os.path.exists(USERS_JSON_PATH):
            try:
                with open(USERS_JSON_PATH, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return []
        return []

    def login(self, instance):
        email = self.email_field.text.strip()
        password = self.password_field.text.strip()

        if not email or not password:
            toast("Please enter email and password")
            return

        users = self.load_users()
        if not users:
            toast("No users registered. Please register an account.")
            return

        hashed_input_password = hashlib.sha256(password.encode()).hexdigest()

        for user in users:
            if user.get("email") == email:
                if user.get("password") == hashed_input_password:
                    app = MDApp.get_running_app()
                    app.current_user = user.get("username")

                    # Ensure matches_history/{username} exists
                    user_history_dir = os.path.join(MATCH_BASE_DIR, app.current_user)
                    os.makedirs(user_history_dir, exist_ok=True)

                    toast(f"Welcome back, {app.current_user}!")
                    self.manager.current = 'home'
                    return
                else:
                    toast("Incorrect password")
                    return

        toast("User with this email not found")

    def go_to_register(self, instance):
        self.manager.current = 'register'
