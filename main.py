from kivy.app import App
from kivy.uix.checkbox import CheckBox
import storage


class GoCardApp(App):

    def build(self):
        storage.create_tables()


    def on_pause(self):
        pass
        return True

    def on_resume(self):
        pass


if __name__ == '__main__':
    GoCardApp().run()
