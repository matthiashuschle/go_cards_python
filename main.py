#!/usr/bin/env python
import os
import logging
from traceback import format_exc
from kivy.app import App
from kivy import platform
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder
from kivy.properties import StringProperty, OptionProperty, \
    NumericProperty, BooleanProperty, ReferenceListProperty, \
    ListProperty, ObjectProperty, DictProperty
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.button import Button
from kivy.uix.recyclegridlayout import RecycleGridLayout
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.recycleview import RecycleView
from kivy.logger import Logger
from plyer import storagepath

from debug import setup_logging, log_time
import storage
from learn_screen import *
from manage_screen import *
from cardset_screen import *
from debug_screen import *

#Window.size = (480, 768)


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

#
# class PopupLabelCell(Label):
#     pass
#
#
# class EditStatePopup(Popup):
#
#     def __init__(self, obj, **kwargs):
#         super(EditStatePopup, self).__init__(**kwargs)
#         self.populate_content(obj)
#
#     def populate_content(self, obj):
#         for x in range(len(obj.table_header.col_headings)):
#             self.container.add_widget(PopupLabelCell(text=obj.table_header.col_headings[x]))
#             textinput = TextInput(text=str(obj.row_data[x]))
#             if x == 0:
#                 textinput.readonly = True
#             self.container.add_widget(textinput)
#
#
# class SelectableRecycleGridLayout(FocusBehavior, LayoutSelectionBehavior,
#                                   RecycleGridLayout):
#     ''' Adds selection and focus behaviour to the view. '''
#
#     selected_row = NumericProperty(0)
#     obj = ObjectProperty(None)
#
#     def get_nodes(self):
#         nodes = self.get_selectable_nodes()
#         if self.nodes_order_reversed:
#             nodes = nodes[::-1]
#         if not nodes:
#             return None, None
#
#         selected = self.selected_nodes
#         if not selected:    # nothing selected, select the first
#             self.selected_row = 0
#             self.select_row(nodes)
#             return None, None
#
#         if len(nodes) == 1:     # the only selectable node is selected already
#             return None, None
#
#         last = nodes.index(selected[-1])
#         self.clear_selection()
#         return last, nodes
#
#     def select_next(self, obj):
#         ''' Select next row '''
#         self.obj = obj
#         last, nodes = self.get_nodes()
#         if not nodes:
#             return
#
#         if last == len(nodes) - 1:
#             self.selected_row = nodes[0]
#         else:
#             self.selected_row = nodes[last + 1]
#
#         self.selected_row += self.obj.total_col_headings
#         self.select_row(nodes)
#
#     def select_previous(self, obj):
#         ''' Select previous row '''
#         self.obj = obj
#         last, nodes = self.get_nodes()
#         if not nodes:
#             return
#
#         if not last:
#             self.selected_row = nodes[-1]
#         else:
#             self.selected_row = nodes[last - 1]
#
#         self.selected_row -= self.obj.total_col_headings
#         self.select_row(nodes)
#
#     def select_current(self, obj):
#         ''' Select current row '''
#         self.obj = obj
#         last, nodes = self.get_nodes()
#         if not nodes:
#             return
#
#         self.select_row(nodes)
#
#     def select_row(self, nodes):
#         col = self.obj.rv_data[self.selected_row]['range']
#         for x in range(col[0], col[1] + 1):
#             self.select_node(nodes[x])
#
#
# class SelectableButton(RecycleDataViewBehavior, Button):
#     ''' Add selection support to the Button '''
#     index = None
#     selected = BooleanProperty(False)
#     selectable = BooleanProperty(True)
#
#     def refresh_view_attrs(self, rv, index, data):
#         ''' Catch and handle the view changes '''
#
#         self.index = index
#         return super(SelectableButton, self).refresh_view_attrs(rv, index, data)
#
#     def on_touch_down(self, touch):
#         ''' Add selection on touch down '''
#         if super(SelectableButton, self).on_touch_down(touch):
#             return True
#         if self.collide_point(*touch.pos) and self.selectable:
#             print("on_touch_down: self=", self)
#             return self.parent.select_with_touch(self.index, touch)
#
#     def apply_selection(self, rv, index, is_selected):
#         ''' Respond to the selection of items in the view. '''
#         self.selected = is_selected
#         self.text_size = self.size
#         if index == rv.data[index]['range'][0]:
#             self.halign = 'right'
#         else:
#             self.halign = 'left'
#
#
# class RV(RecycleView):
#     row_data = ()
#     rv_data = ListProperty([])
#     total_col_headings = 5
#     cols_minimum = 5
#     row_controller = ObjectProperty(None)
#     table_header = ObjectProperty(None)
#
#     def __init__(self, **kwargs):
#         super(RV, self).__init__(**kwargs)
#         self.database_connection()
#         self.get_states()
#         Clock.schedule_once(self.set_default_first_row, .0005)
#         self._request_keyboard()
#
#     def database_connection(self):
#         self.db = lite.connect('chinook.db')
#         Logger.info(str(self.db))
#         self.db_cursor = self.db.cursor()
#
#     def _request_keyboard(self):
#         self._keyboard = Window.request_keyboard(
#             self._keyboard_closed, self, 'text'
#         )
#         if self._keyboard.widget:
#             # If it exists, this widget is a VKeyboard object which you can use
#             # to change the keyboard layout.
#             pass
#         self._keyboard.bind(on_key_down=self._on_keyboard_down)
#
#     def _keyboard_closed(self):
#         self._keyboard.unbind(on_key_down=self._on_keyboard_down)
#         self._keyboard = None
#
#     def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
#         if keycode[1] == 'down':    # keycode[274, 'down'] pressed
#             # Respond to keyboard down arrow pressed
#             self.display_keystrokes(keyboard, keycode, text, modifiers)
#             self.row_controller.select_next(self)
#
#         elif keycode[1] == 'up':    # keycode[273, 'up] pressed
#             # Respond to keyboard up arrow pressed
#             self.display_keystrokes(keyboard, keycode, text, modifiers)
#             self.row_controller.select_previous(self)
#
#         elif len(modifiers) > 0 and modifiers[0] == 'ctrl' and text == 'e':     # ctrl + e pressed
#             # Respond to keyboard ctrl + e pressed, and call Popup
#             self.display_keystrokes(keyboard, keycode, text, modifiers)
#             self.on_keyboard_select()
#
#         # Keycode is composed of an integer + a string
#         # If we hit escape, release the keyboard
#         if keycode[1] == 'escape':
#             keyboard.release()
#
#         # Return True to accept the key. Otherwise, it will be used by
#         # the system.
#         return True
#
#     def display_keystrokes(self, keyboard, keycode, text, modifiers):
#         print("\nThe key", keycode, "have been pressed")
#         print(" - text is %r" % text)
#         print(" - modifiers are %r" % modifiers)
#
#     def on_keyboard_select(self):
#         ''' Respond to keyboard event to call Popup '''
#
#         # setup row data for Popup
#         self.setup_row_data(self.rv_data[self.row_controller.selected_row]['Index'])
#
#         # call Popup
#         self.popup_callback()
#
#     def on_mouse_select(self, instance):
#         ''' Respond to mouse event to call Popup '''
#
#         if self.row_controller.selected_row != instance.index:
#             # Mouse clicked on row is not equal to current selected row
#             self.row_controller.selected_row = instance.index
#
#             # Hightlight mouse clicked/selected row
#             self.row_controller.select_current(self)
#
#         # setup row data for Popup
#         self.setup_row_data(self.rv_data[instance.index]['Index'])
#
#         # call Popup
#         self.popup_callback()
#
#         # enable keyboard request
#         self._request_keyboard()
#
#     def setup_row_data(self, value):
#         self.db_cursor.execute("SELECT * FROM customers WHERE CustomerId=?", value)
#         self.row_data = self.db_cursor.fetchone()
#
#     def popup_callback(self):
#         ''' Instantiate and Open Popup '''
#         popup = EditStatePopup(self)
#         popup.open()
#
#     def set_default_first_row(self, dt):
#         ''' Set default first row as selected '''
#         self.row_controller.select_next(self)
#
#     def get_states(self):
#         self.db_cursor.execute("SELECT * FROM customers ORDER BY CustomerId ASC")
#         rows = self.db_cursor.fetchall()
#
#         data = []
#         low = 0
#         high = self.total_col_headings - 1
#         for row in rows:
#             for i in range(len(row)):
#                 data.append([row[i], row[0], [low, high]])
#             low += self.total_col_headings
#             high += self.total_col_headings
#
#         self.rv_data = [{'text': str(x[0]), 'Index': str(x[1]), 'range': x[2], 'selectable': True} for x in data]



# class NavbarButton(Button):
#     pass
#
#
# class MainScreen(BoxLayout):
#
#     navbar = ObjectProperty(None)
#     content_frame = ObjectProperty(None)
#
#     def __init__(self, *args, **kwargs):
#         super(MainScreen, self).__init__(*args, **kwargs)
#         self.table = None
#
#     def build_nav_bar(self):
#         self.navbar.clear_widgets()
#         button_import = NavbarButton(text='Import', font_size=14)
#         button_new_set = NavbarButton(text='New Set', font_size=14)
#         self.navbar.add_widget(button_import)
#         self.navbar.add_widget(button_new_set)
#
#     def build_content_table(self):
#         self.content_frame.clear_widgets()
#         self.table = Table()
#         self.content_frame.add_widget(self.table)
#
#     def display_start_content(self):
#         self.build_content_table()
#         self.build_nav_bar()
#
#
# class TestApp(App):
#     title = "test"
#     storage = None
#
#     def build(self):
#         if TestApp.storage is None:
#             TestApp.storage = storage.Storage()
#         screen = MainScreen()
#         screen.display_start_content()
#         return screen

