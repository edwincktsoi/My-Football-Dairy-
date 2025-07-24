# main.py

from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager
from kivy.core.window import Window


class FootballApp(MDApp):
    current_user = None  # Property to store the currently logged-in user

    def build(self):
        Window.size = (400, 750)

        # Import screens here to avoid potential circular dependencies
        from screens.login_screen import LoginScreen
        from screens.register_screen import RegisterScreen
        from screens.home_screen import HomeScreen
        from screens.player_screen import PlayerScreen
        from screens.add_stat_screen import AddStatScreen

        sm = MDScreenManager()
        self.theme_cls.primary_palette = "Green"
        self.theme_cls.accent_palette = "Blue"
        self.theme_cls.theme_style = "Dark" # Or "Light"

        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(RegisterScreen(name='register'))
        sm.add_widget(HomeScreen(name='home'))
        sm.add_widget(PlayerScreen(name='player'))
        sm.add_widget(AddStatScreen(name='add_stat'))  # Register new screen
        sm.current = 'login'
        return sm

if __name__ == '__main__':
    FootballApp().run()
