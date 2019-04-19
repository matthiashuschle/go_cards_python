import os
import re
import csv
from kivy.logger import Logger
from kivy.metrics import dp, sp
from kivy.properties import BooleanProperty, ObjectProperty
from kivy.uix.screenmanager import Screen
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.gridlayout import GridLayout
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recycleview import RecycleView
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from debug import log_time
from common import get_screen, set_screen_active, PopupLabelCell, CardsetPopup, CARD_FROM_STRING


class MergeCardSetsPopup(Popup):

    def merge(self):
        set_name = self.ids['new_name'].text.strip()[:100]
        if not len(set_name):
            self.alert('No name given!')
            return
        # sanitize
        set_name = re.sub(r'[\W]', '', set_name)
        self.ids['new_name'].text = set_name
        duplicates = get_screen('manage').check_for_duplicates({set_name})
        if len(duplicates):
            self.alert('set already exist:' + os.linesep + ', '.join(duplicates))
            return
        get_screen('manage').act_on_merge(set_name)
        self.dismiss()

    def alert(self, msg):
        try:
            self.ids['alert'].text = msg
        except KeyError:
            pass


class ImportCardSetPopup(Popup):

    container = ObjectProperty(None)

    def __init__(self, import_dir, **kwargs):
        super().__init__(**kwargs)
        self.import_dir = import_dir
        self.ids['info_text'].text = os.linesep.join([
            'Enter card set name,',
            'leave blank to skip.',
            'Imports from',
            import_dir
        ])
        csvfiles = self.get_existing_files()
        self.file_mapping = {file: 'file_to_%i' % i for i, file in enumerate(csvfiles)}
        for filename in csvfiles:
            self.container.add_widget(PopupLabelCell(text=filename, font_size=sp(8)))
            set_name = re.sub(r'[\W]', '', filename[:-4])
            text_input = TextInput(text=set_name, font_size=sp(8))
            self.container.add_widget(text_input)
            self.ids[self.file_mapping[filename]] = text_input
        if not len(csvfiles):
            self.alert('no csv files found')

    def get_existing_files(self):
        csvfiles = sorted([os.path.basename(x) for x in os.listdir(self.import_dir) if x.lower().endswith('.csv')])
        return csvfiles

    def alert(self, msg):
        try:
            self.ids['alert'].text = msg
        except KeyError:
            pass

    def do_import(self):
        to_import = {}
        for filename, field_id in self.file_mapping.items():
            set_name = self.ids[field_id].text.strip()[:100]
            if not len(set_name):
                continue
            # sanitize
            set_name = re.sub(r'[\W]', '', set_name)
            to_import[filename] = set_name
            self.ids[field_id].text = set_name
        if not len(to_import):
            self.alert('nothing to do!')
            return
        set_names = set(to_import.values())
        if len(set_names) != len(to_import):
            self.alert('there are duplicates in the set names!')
            return
        duplicates = get_screen('manage').check_for_duplicates(set_names)
        if len(duplicates):
            self.alert('following sets already exist:' + os.linesep + ', '.join(duplicates))
        try:
            self.alert('importing...')
            get_screen('manage').act_on_import(to_import)
            self.dismiss()
        except OSError:
            self.alert('something went wrong!')
            return


class SelectableRecycleBoxLayout(FocusBehavior,
                                 RecycleBoxLayout):
    """ Adds selection and focus behaviour to the view. """


class SelectableLabel(RecycleDataViewBehavior, GridLayout):
    """ Add selection support to the Label """
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)
    cols = 4

    def on_checkbox_active(self, _, value):
        self.selected = value

    def refresh_view_attrs(self, rv, index, data):
        """ Catch and handle the view changes """
        self.index = index
        self.ids['id_label1'].text = data['set_name']
        self.ids['id_label2'].text = str(data['card_count'])
        self.selected = data['active']
        self.ids['cb_active'].active = data['active']
        self.ids['cb_active'].bind(active=self.on_checkbox_active)
        return super(SelectableLabel, self).refresh_view_attrs(
            rv, index, data)

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
        } for x in self.storage.card_sets.values()]
        SelectableRecycleBoxLayout.selected_nodes = [
            i for i, card_set in enumerate(self.storage.card_sets.values()) if card_set.active]

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
        with log_time('manage - get selected'):
            selected_set_ids = self.rv.get_selected()
        with log_time('manage - update_cards'):
            get_screen('learn').update_cards(selected_set_ids)
        if len(selected_set_ids):
            set_screen_active('learn')

    def create_new_card_set(self):
        NewCardsetPopup('Create Card Set', storage=self.storage).open()

    def act_on_new_set(self, value_dict):
        self.storage.add_new_set(value_dict)
        self.rv.reset_data()

    def merge_card_sets(self):
        selected_set_ids = self.rv.get_selected()
        if not len(selected_set_ids):
            return
        MergeCardSetsPopup().open()

    def act_on_merge(self, set_name):
        selected_set_ids = self.rv.get_selected()
        self.storage.merge_sets(selected_set_ids, set_name)
        self.rv.reset_data()

    def cardset_import(self):
        ImportCardSetPopup(self.import_dir).open()

    def check_for_duplicates(self, set_names):
        existing_names = set(self.storage.card_sets.keys())
        overlap = set_names & existing_names
        return overlap

    def act_on_import(self, to_import):
        for filename, set_name in to_import.items():
            full_path = os.path.join(self.import_dir, filename)
            cardset = self.storage.add_new_set({'name': set_name})
            cards = []
            allowed_fields = ['left', 'right', 'left_info', 'right_info',
                              'last_seen', 'streak', 'hidden_until']
            with open(full_path, 'r') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    value_dict = {}
                    for key, val in row.items():
                        if key not in allowed_fields:
                            continue
                        if val is None:
                            continue
                        val = val.strip()
                        if not len(val):
                            continue
                        if key in CARD_FROM_STRING:
                            val = CARD_FROM_STRING[key](val)
                        value_dict[key] = val
                    if len(value_dict):
                        cards.append(value_dict)
            self.storage.add_many_cards(cards, cardset)
        self.rv.reset_data()
