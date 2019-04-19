import os
import datetime
import re
import csv
from kivy.uix.screenmanager import Screen
from kivy.logger import Logger
from kivy.properties import ObjectProperty
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.gridlayout import GridLayout
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recycleview import RecycleView
from kivy.properties import BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from common import (
    set_screen_active, get_screen, CardsetPopup, CardPopup,
    CARD_TO_STRING, DeletePopup)


class ViewPopup(Popup):

    def set_options(self):
        options = {
            'hide_known': self.ids['hide_known'].active,
            'by_streak': self.ids['cb_streak'].active,
            'by_left': self.ids['cb_left'].active,
            'by_right': self.ids['cb_right'].active
        }
        get_screen('cardset').act_on_view(options)
        self.dismiss()


class CopyCardSetPopup(Popup):

    def __init__(self, existing_names, **kwargs):
        super().__init__(**kwargs)
        self.existing_names = existing_names

    def alert(self, msg):
        try:
            self.ids['alert'].text = msg
        except KeyError:
            pass

    def copy(self):
        new_name = self.ids['new_name'].text.strip()
        new_name = re.sub(r'[\W]', '', new_name)
        self.ids['new_name'].text = new_name
        if not len(new_name):
            self.alert('new has no valid characters!')
            return
        if new_name in self.existing_names:
            self.alert('A set of that name already exists!')
            return
        get_screen('cardset').act_on_copy(
            new_name,
            shuffle=self.ids['cb_shuffle'].active,
            swap=self.ids['cb_swap'].active,
            reset=self.ids['cb_reset'].active,
            apply_qi=self.ids['cb_apply_qi'].active,
            apply_ai=self.ids['cb_apply_ai'].active,
        )
        self.dismiss()


class ExportCardSetPopup(Popup):

    def __init__(self, export_dir, **kwargs):
        super().__init__(**kwargs)
        self.ids['info_text'].text = os.linesep.join([
            'Enter the filename without ending.',
            'Exports to:',
            export_dir
        ])

    def alert(self, msg):
        try:
            self.ids['alert'].text = msg
        except KeyError:
            pass

    def export(self):
        filename = self.ids['filename'].text.strip()[:100]
        if not len(filename):
            self.alert('please enter a filename!')
            return
        # sanitize
        sanitized = re.sub(r'[\W]', '', filename)
        if sanitized != filename:
            self.ids['filename'].text = sanitized
            self.alert('please check the filename again!')
            return
        try:
            get_screen('cardset').act_on_export(filename)
            self.dismiss()
        except OSError:
            self.alert('something went wrong!')
            return


class NewCardPopup(CardPopup):

    def act_on_save(self, value_dict):
        get_screen('cardset').act_on_new_card(value_dict)


class EditCardSetPopup(CardsetPopup):

    def act_on_save(self, value_dict):
        for field, value in value_dict.items():
            setattr(self.db_object, field, value)
        get_screen('cardset').act_on_cardset_edit(self.db_object)


class FullEditCardPopup(CardPopup):

    def act_on_save(self, value_dict):
        for field, value in value_dict.items():
            setattr(self.db_object, field, value)
        get_screen('cardset').act_on_card_edit(self.db_object)

    def delete(self):
        DeletePopup(self.db_object.left, callback=self.delete_callback).open()

    def delete_callback(self):
        get_screen('cardset').act_on_card_delete(self.db_object)
        self.dismiss()


class CardListLabel(RecycleDataViewBehavior, BoxLayout):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.card_id = None

    def refresh_view_attrs(self, rv, index, data):
        """ Catch and handle the view changes """
        # self.index = index
        self.card_id = data['card_id']
        btn_left = self.ids['btn_left']
        btn_right = self.ids['btn_right']
        btn_left.text = data['question']
        btn_right.text = data['answer']
        if index % 2 == 0:
            btn_left.background_color = [0.1, 0.1, 0.1, 1.]
            btn_right.background_color = [0.1, 0.1, 0.1, 1.]
        else:
            btn_left.background_color = [0., 0., 0., 1.]
            btn_right.background_color = [0., 0., 0., 1.]
        return super(CardListLabel, self).refresh_view_attrs(
            rv, index, data)

    def edit(self):
        print('in edit')
        get_screen('cardset').edit_card(self.card_id)


class CardRV(RecycleView):

    def __init__(self, storage, **kwargs):
        super(CardRV, self).__init__(**kwargs)
        self.storage = storage
        Logger.info('in RV')


class CardSetScreen(Screen):

    box_card_table = ObjectProperty(None)

    def __init__(self, storage, export_dir, **kwargs):
        super().__init__(**kwargs)
        self.storage = storage
        self.export_dir = export_dir
        self.current_set = None
        self.current_cards = None
        self.hide_known = False
        self.rv = CardRV(storage)
        self.box_card_table.add_widget(self.rv)
        # self.card_table = CardContainer(storage)
        # self.ids.card_table.add_widget(self.card_table)
        Logger.info('in CardSetScreen')

    def get_current_card_by_id(self, card_id):
        target_card = None
        for card in self.current_cards:
            if card.card_id == card_id:
                target_card = card
                break
        if target_card is None:
            raise KeyError('no Card with ID %i.' % card_id)
        return target_card

    def set_set_name(self, set_name):
        self.ids['title'].text = set_name
        self.current_set = self.storage.card_sets.get(set_name, None)
        if self.current_set is None:
            return set_screen_active('manage')
        self.update_cards()

    def update_cards(self):
        self.current_cards = [x.card for x in self.storage.cards.values() if x.card_set == self.current_set]
        self._set_cards(self.current_cards)

    def _set_cards(self, cards):
        self.rv.data = [{
            'card_id': card.card_id,
            'question': card.left,
            'answer': card.right
        } for card in cards]

    def edit_card(self, card_id):
        """ Card edit popup """
        FullEditCardPopup('Edit Card', db_object=self.get_current_card_by_id(card_id)).open()

    def act_on_card_edit(self, card_db_object):
        """ Digest result of card edit popup. """
        self.storage.update_card_queue.put(card_db_object.card_id)
        self.update_cards()

    def new_card(self):
        """ Card edit popup """
        NewCardPopup('Create Card', default_vals={
            'left_info': self.current_set.left_info,
            'right_info': self.current_set.right_info,
        }).open()

    def act_on_new_card(self, value_dict):
        """ Digest result of card edit popup. """
        self.storage.add_new_card(value_dict, self.current_set)
        self.update_cards()

    def edit_cardset(self):
        """ Card edit popup """
        EditCardSetPopup('Edit Card Set', db_object=self.current_set, storage=self.storage).open()

    def act_on_cardset_edit(self, cardset_db_object):
        """ Digest result of card edit popup. """
        self.storage.update_set(cardset_db_object.cardset_id)
        self.ids['title'].text = cardset_db_object.name

    def export_popup(self):
        """ Export Card Set popup """
        ExportCardSetPopup(self.export_dir).open()

    def act_on_export(self, filename):
        """ Export Card Set after receiving the filename in the popup. """
        with open(os.path.join(self.export_dir, filename + '.csv'), 'w', newline='') as csvfile:
            fieldnames = ['left', 'right', 'left_info', 'right_info', 'last_seen', 'streak', 'hidden_until']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for card in self.current_cards:
                card_dict = card.to_dict()
                for field, conversion in CARD_TO_STRING.items():
                    card_dict[field] = conversion(card_dict[field])
                writer.writerow({x: y for x, y in card_dict.items() if x in fieldnames})

    def copy_popup(self):
        """ Copy Card Set popup.

        With flags for shuffle, swap, reset, apply left/right info.
        """
        CopyCardSetPopup(existing_names=set(self.storage.card_sets.keys())).open()

    def act_on_copy(self, new_name, shuffle=False, swap=False, reset=False,
                    apply_qi=False, apply_ai=False):
        self.storage.copy_set_to(self.current_set, new_name, shuffle=shuffle, swap=swap,
                                 reset=reset, apply_qi=apply_qi, apply_ai=apply_ai)
        get_screen('manage').rv.reset_data()
        self.set_set_name(new_name)

    def delete_set_popup(self):
        DeletePopup(
            self.current_set.name, callback=self.act_on_delete).open()

    def act_on_delete(self):
        self.storage.delete_set(self.current_set)
        get_screen('manage').rv.reset_data()
        set_screen_active('manage')

    def act_on_card_delete(self, card):
        self.storage.delete_card(card)
        self.update_cards()

    def view_popup(self):
        ViewPopup().open()

    def act_on_view(self, options):
        cards = [x for x in self.current_cards]
        if options['hide_known']:
            now = datetime.datetime.utcnow()
            cards = [x for x in cards if x.hidden_until < now]
        if options['by_streak']:
            cards = sorted(cards, key=lambda x: x.streak)
        if options['by_left']:
            cards = sorted(cards, key=lambda x: x.left)
        if options['by_right']:
            cards = sorted(cards, key=lambda x: x.right)
        self._set_cards(cards)
