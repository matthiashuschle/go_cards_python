from kivy.uix.screenmanager import Screen
from kivy.logger import Logger


class CardSetScreen(Screen):

    current_set_name = None
    set_data = None

    def __init__(self, storage, export_dir, **kwargs):
        super().__init__(**kwargs)
        self.storage = storage
        self.export_dir = export_dir
        Logger.info('in CardSetScreen')

    def on_pre_enter(self, *args):
        if self.current_set_name is None:
            return
        set_data = [x for x in self.storage.card_sets if x.name == self.current_set_name]
        if not len(set_data):
            set_data = None
        else:
            set_data = set_data[0]
        CardSetScreen.set_data = set_data
