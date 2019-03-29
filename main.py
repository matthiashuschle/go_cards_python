from kivy.app import App
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
import sqlite3 as lite
import re

import storage
from recycleview_manage import *

Window.size = (480, 768)


COLORS = {
    'base': (0.145, 0.431, 0.369),
    'light': (0.29, 0.569, 0.188),
    'dark': (0.173, 0.278, 0.439)
}
STORAGE = storage.Storage()

# Create both screens. Please note the root.manager.current: this is how
# you can control the ScreenManager from kv. Each screen has by default a
# property manager that gives you the instance of the ScreenManager used.
Builder.load_file('general.kv')
Builder.load_file('new_set.kv')
Builder.load_file('recycleview_manage.kv')
Builder.load_string("""
<ManageScreen>:
    BoxLayout:
        orientation: 'vertical'

        BoxLayout:
            orientation: 'horizontal'
            spacing: 1
            padding: 1
            size_hint_y: 1
            NavbarButton:
                text: 'Import'
            NavbarButton:
                text: 'NewSet'
                on_press: root.create_new_card_set()
            NavbarButton:
                text: 'Learn'
                on_press: root.open_learn()

        BoxLayout:
            id: set_table
            orientation: 'vertical'
            size_hint_y: 11
            
<CardSetScreen>:
    BoxLayout:
        orientation: 'vertical'

        BoxLayout:
            orientation: 'horizontal'
            spacing: 1
            padding: 1
            size_hint_y: 1
            NavbarButton:
                text: 'Back'
                on_press: root.manager.current = 'manage'

<LearnScreen>:

    BoxLayout:
        orientation: 'vertical'

        BoxLayout:
            id: navbar
            orientation: 'horizontal'
            spacing: 1
            padding: 1
            size_hint_y: 1
            NavbarButton:
                text: 'Back'
                on_press: root.manager.current = 'manage'
            NavbarButton:
                text: 'Delay 10hrs'
                on_press: root.delay_current()
            NavbarButton:
                text: 'Edit'
                on_press: root.edit_current()

        BoxLayout:
            id: questions
            orientation: 'vertical'
            size_hint_y: 8
            HiddenButton:
                id: q_next
                text: 'foo'
                color: .6, .6, .6, 1.
                font_size: 14
                on_press: root.reveal()
            HiddenButton:
                id: q_this
                text: 'bar'
                font_size: 20
                on_press: root.reveal()
            HiddenButton:
                id: answer
                text: 'hidden answer'
                font_size: 20
                on_press: root.reveal()
                
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: 3
            BoxLayout:
                orientation: 'horizontal'
                spacing: 1
                padding: 1
                NavbarButton:
                    background_color: 0.173, 0.278, 0.439, 1.
                    text: 'wrong'
                    on_press: root.wrong_answer()
                NavbarButton:
                    background_color: 0.29, 0.569, 0.188, 1.
                    text: 'correct'
                    on_press: root.right_answer()
""")


# Declare both screens
class ManageScreen(Screen):

    def __init__(self, storage, **kwargs):
        super(ManageScreen, self).__init__(**kwargs)
        self.storage = storage
        Logger.info('in ManageScreen')
        self.table = Table(self.storage)
        self.ids.set_table.add_widget(self.table)

    def open_learn(self):
        LearnScreen.selected_sets = Table.rv.get_selected()
        if len(LearnScreen.selected_sets):
            sm.current = 'learn'

    def create_new_card_set(self):
        EditStatePopup(self.storage).open()


class CardSetScreen(Screen):

    current_set_name = None
    set_data = None

    def __init__(self, storage, **kwargs):
        super().__init__(**kwargs)
        self.storage = storage
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


class LearnScreen(Screen):

    selected_sets = []
    card_data = []

    def __init__(self, storage, **kwargs):
        super().__init__(**kwargs)
        self.storage = storage
        Logger.info('in LearnScreen')

    def on_pre_enter(self, *args):
        self.storage.set_sets_active(self.selected_sets)
        card_data = [
            x for x in self.storage.cards if x.card_set.name in self.selected_sets]
        # ToDo: filter and sort
        LearnScreen.card_data = card_data
        self.update_questions()

    @staticmethod
    def _wrap_question(question, info):
        info_str = '' if info is None or not len(info) else '(%s)' % info
        return '%s %s' % (info_str, question)

    def update_questions(self):
        self.ids['answer'].text = ''
        self.ids['q_this'].text = ''
        self.ids['q_next'].text = ''
        if self.current_card is not None:
            self.ids['q_this'].text = self._wrap_question(
                self.current_card.left, self.current_card.left_info)
        if self.next_card is not None:
            self.ids['q_next'].text = '(Upcoming: %s)' % self._wrap_question(
                self.next_card.left, self.next_card.left_info)

    @property
    def current_card(self):
        """

        :rtype: storage.Card
        """
        if len(self.card_data):
            return self.card_data[0]

    @property
    def next_card(self):
        """

        :rtype: storage.Card
        """
        if len(self.card_data) > 1:
            return self.card_data[1]

    def reveal(self):
        if self.current_card is not None:
            self.ids['answer'].text = self.current_card.right

    def wrong_answer(self):
        pass

    def right_answer(self):
        pass

    def delay_current(self):
        pass

    def edit_current(self):
        pass


# Create the screen manager
sm = ScreenManager()
sm.transition = SlideTransition(duration=.2)
sm.add_widget(ManageScreen(STORAGE, name='manage'))
sm.add_widget(LearnScreen(STORAGE, name='learn'))
sm.add_widget(CardSetScreen(STORAGE, name='cardset'))


class GoCardsApp(App):

    def build(self):
        return sm


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

