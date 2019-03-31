from kivy.logger import Logger
from kivy.properties import BooleanProperty
from kivy.uix.screenmanager import Screen
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.gridlayout import GridLayout
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recycleview import RecycleView
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from common import get_screen, set_screen_active, PopupLabelCell, CardsetPopup


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
        get_screen('cardset').set_set_name(
            get_screen('manage').rv.data[self.index]['set_name']
        )
        set_screen_active('cardset')


class CardSetRV(RecycleView):

    def __init__(self, storage, **kwargs):
        super(CardSetRV, self).__init__(**kwargs)
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
        return [self.data[ix]['set_name'] for node, ix in
                self.ids['rv_layout'].view_indices.items() if node.selected]


class NewCardsetPopup(CardsetPopup):

    def act_on_save(self, value_dict):
        get_screen('manage').act_on_new_set(value_dict)


class ManageScreen(Screen):

    def __init__(self, storage, import_dir, **kwargs):
        super().__init__(**kwargs)
        self.storage = storage
        self.import_dir = import_dir
        Logger.info('in ManageScreen')
        self.rv = CardSetRV(storage)
        self.ids.card_set_table.add_widget(self.rv)

    def open_learn(self):
        selected_set_ids = self.rv.get_selected()
        get_screen('learn').update_cards(selected_set_ids)
        if len(selected_set_ids):
            set_screen_active('learn')

    def create_new_card_set(self):
        NewCardsetPopup('Create Card Set', storage=self.storage).open()

    def act_on_new_set(self, value_dict):
        self.storage.add_new_set(value_dict)
        self.rv.reset_data()
