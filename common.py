from kivy.app import App
from kivy.uix.label import Label


class PopupLabelCell(Label):
    pass


def get_screen_manager():
    return App.get_running_app().root


def get_screen(name):
    return get_screen_manager().get_screen(name)


def set_screen_active(name):
    get_screen_manager().current = name
