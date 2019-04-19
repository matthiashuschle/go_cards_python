#!/usr/bin/env python
import os
from traceback import format_exc
from kivy.app import App
from kivy import platform
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, SlideTransition
from plyer import storagepath

from debug import setup_logging, log_time
import storage
from learn_screen import *
from manage_screen import *
from cardset_screen import *
from debug_screen import *


COLORS = {
    'base': (0.145, 0.431, 0.369),
    'light': (0.29, 0.569, 0.188),
    'dark': (0.173, 0.278, 0.439)
}

Builder.load_file('common.kv')
Builder.load_file('manage.kv')
Builder.load_file('learn.kv')
Builder.load_file('cardset.kv')
Builder.load_file('debug.kv')


class GoCardsApp(App):

    def build(self):
        # Create the screen manager
        sm = ScreenManager()
        sm.transition = SlideTransition(duration=.2)
        try:
            root_dir, import_dir, export_dir = self.init_data_folder()
        except Exception as exc:
            sm.add_widget(DebugScreen(format_exc(), name='debug'))
            return sm
        setup_logging(os.path.join(root_dir, 'debug.log'))
        with log_time('setup storage'):
            storage.set_database_dir(root_dir)
            storage_handler = storage.Storage()
        print('using folders:', root_dir, import_dir, export_dir)
        with log_time('create widget manage'):
            sm.add_widget(ManageScreen(storage_handler, import_dir, name='manage'))
        with log_time('create widget learn'):
            sm.add_widget(LearnScreen(storage_handler, name='learn'))
        with log_time('create widget cardset'):
            sm.add_widget(CardSetScreen(storage_handler, export_dir, name='cardset'))
        return sm

    def init_data_folder(self):
        root_folder = self.user_data_dir
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE
            ])
            root_folder = os.path.join(storagepath.get_external_storage_dir(), 'gocards')
        import_dir = os.path.join(root_folder, 'import')
        export_dir = os.path.join(root_folder, 'export')
        os.makedirs(import_dir, exist_ok=True)
        os.makedirs(export_dir, exist_ok=True)
        if import_dir is None or not os.path.isdir(import_dir):
            raise OSError('could not create import/export folders')
        return root_folder, import_dir, export_dir


if __name__ == '__main__':
    GoCardsApp().run()
