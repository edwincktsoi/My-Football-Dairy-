# screens/player_screen.py
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.boxlayout import MDBoxLayout

class PlayerScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = MDBoxLayout(orientation='vertical', padding=20, spacing=20)

        label = MDLabel(
            text="Player Statistics",
            halign='center',
            theme_text_color='Primary',
            font_style='H5'
        )

        back_btn = MDRaisedButton(
            text="Back to Home",
            pos_hint={"center_x": 0.5},
            on_release=self.go_home
        )

        layout.add_widget(label)
        layout.add_widget(back_btn)
        self.add_widget(layout)

    def go_home(self, instance):
        self.manager.current = 'home'
