# screens/home_screen.py

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton

class HomeScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = MDBoxLayout(orientation='vertical', padding=40, spacing=20)

        layout.add_widget(MDLabel(
            text="Welcome to Football Stat Tracker",
            halign="center",
            font_style="H5"
        ))

        player_btn = MDRaisedButton(
            text="View Player Stats",
            pos_hint={"center_x": 0.5},
            on_release=self.go_to_player
        )

        stat_btn = MDRaisedButton(
            text="Add Personal Stat",
            pos_hint={"center_x": 0.5},
            on_release=self.go_to_add_stat
        )

        logout_btn = MDRaisedButton(
            text="Logout",
            pos_hint={"center_x": 0.5},
            on_release=self.logout,
            md_bg_color=self.theme_cls.error_color
        )

        layout.add_widget(player_btn)
        layout.add_widget(stat_btn)
        layout.add_widget(logout_btn)

        self.add_widget(layout)

    def go_to_player(self, instance):
        self.manager.current = 'player'

    def go_to_add_stat(self, instance):
        self.manager.current = 'add_stat'

    def logout(self, instance):
        app = MDApp.get_running_app()
        app.current_user = None
        self.manager.current = 'login'
