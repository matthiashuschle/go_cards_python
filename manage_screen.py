from kivy.logger import Logger
from kivy.properties import BooleanProperty, ObjectProperty
from kivy.uix.screenmanager import Screen
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recycleview import RecycleView
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from common import get_screen, set_screen_active, PopupLabelCell


class SelectableRecycleBoxLayout(FocusBehavior, LayoutSelectionBehavior,
                                 RecycleBoxLayout):
    """ Adds selection and focus behaviour to the view. """


class SelectableLabel(RecycleDataViewBehavior, GridLayout):
    """ Add selection support to the Label """
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)
    cols = 3

    def refresh_view_attrs(self, rv, index, data):
        """ Catch and handle the view changes """
        self.index = index
        self.ids['id_label1'].text = data['set_name']
        self.ids['id_label2'].text = str(data['card_count'])
        self.selected = data['active']
        return super(SelectableLabel, self).refresh_view_attrs(
            rv, index, data)

    def on_touch_down(self, touch):
        """ Add selection on touch down """
        if super(SelectableLabel, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        """ Respond to the selection of items in the view. """
        self.selected = is_selected

    def view_set(self):
        # setup car set view screen
        get_screen('cardset').current_set_name = Table.rv.data[self.index]['set_name']
        # switch to card set view
        set_screen_active('cardset')


class RV(RecycleView):

    def __init__(self, storage, **kwargs):
        super(RV, self).__init__(**kwargs)
        self.storage = storage
        Logger.info('in RV')
        self.reset_data()

    def reset_data(self):
        self.data = [{
            'set_name': x.name,
            'card_count': x.card_count,
            'active': x.active
        } for x in self.storage.card_sets]
        SelectableRecycleBoxLayout.selected_nodes = [
            i for i, card_set in enumerate(self.storage.card_sets) if card_set.active]

    def get_selected(self):
        return [Table.rv.data[ix]['set_name'] for node, ix in
                self.ids['rv_layout'].view_indices.items() if node.selected]


class Table(BoxLayout):
    rv = ObjectProperty(None)

    def __init__(self, storage, **kwargs):
        super(Table, self).__init__(**kwargs)
        Logger.info('in Table')
        self.orientation = "vertical"
        Table.rv = RV(storage)
        self.add_widget(self.rv)


class EditStatePopup(Popup):

    def __init__(self, storage, **kwargs):
        super(EditStatePopup, self).__init__(**kwargs)
        self.storage = storage
        self.title = 'Create New Card Set'
        self.populate_content()

    def populate_content(self):
        for field in ['*name', 'description', 'left info', 'right info']:
            self.container.add_widget(PopupLabelCell(text=field))
            textinput = TextInput(text='')
            self.container.add_widget(textinput)

    def save(self):
        # children are reversed
        content = list(reversed([
            thing.text.strip() for i, thing in enumerate(self.container.children)
            if i % 2 == 0
        ]))
        existing_names = set(x.name for x in self.storage.card_sets)
        if not len(content[0]):
            self.ids['alert'].text = 'no name given!'
            return
        if len(content[0]) and content[0] in existing_names:
            self.ids['alert'].text = 'name already exists!'
            return
        self.storage.add_new_set(*content)
        Table.rv.reset_data()
        self.dismiss()


class ManageScreen(Screen):

    def __init__(self, storage, import_dir, **kwargs):
        super().__init__(**kwargs)
        self.storage = storage
        self.import_dir = import_dir
        Logger.info('in ManageScreen')
        self.table = Table(self.storage)
        self.ids.set_table.add_widget(self.table)

    def open_learn(self):
        selected_set_ids = self.table.rv.get_selected()
        get_screen('learn').update_cards(selected_set_ids)
        if len(selected_set_ids):
            set_screen_active('learn')

    def create_new_card_set(self):
        EditStatePopup(self.storage).open()