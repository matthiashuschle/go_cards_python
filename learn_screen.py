import datetime
from kivy.uix.screenmanager import Screen
from kivy.logger import Logger
from kivy.uix.popup import Popup
from kivy.properties import ObjectProperty
from common import set_screen_active, get_screen


class EditCardPopup(Popup):

    id_map = {
        'edit_q': 'left',
        'edit_a': 'right',
        'edit_qi': 'left_info',
        'edit_ai': 'right_info',
        'edit_s': 'streak'
    }

    def __init__(self, card, **kwargs):
        super(EditCardPopup, self).__init__(**kwargs)
        self.card = card
        self.title = 'Edit Card'
        self.populate_content()

    def populate_content(self):
        card_dict = self.card.to_dict()
        for cell_id, db_field in self.id_map.items():
            self.ids[cell_id].text = str(card_dict[db_field])

    def alert(self, msg):
        self.ids['alert'].text = msg

    def save(self):
        card_dict = self.card.to_dict()
        changed = False
        for cell_id, db_field in self.id_map.items():
            new_val = self.ids[cell_id].text.strip()
            if db_field == 'streak':
                try:
                    new_val = int(new_val)
                except ValueError:
                    self.alert('invalid streak!')
                    return
            if new_val != card_dict[db_field]:
                changed = True
                setattr(self.card, db_field, new_val)
        if changed:
            get_screen('learn').act_on_card_edit()
            self.dismiss()
        else:
            self.alert('nothing changed!')

    def cancel(self):
        get_screen('learn').move_current_card_back()
        self.dismiss()


class LearnScreen(Screen):

    set_info_label = ObjectProperty(None)
    selected_sets = []

    def __init__(self, storage, **kwargs):
        super().__init__(**kwargs)
        self.storage = storage
        self.card_data = []
        self.total_cards = None
        Logger.info('in LearnScreen')

    def update_cards(self, selected_sets):
        self.storage.set_sets_active(selected_sets)
        card_data = [x for x in self.storage.cards if x.card_set.name in selected_sets]
        self.total_cards = len(card_data)
        now = datetime.datetime.utcnow()
        card_data = [x for x in card_data if x.hidden_until < now]
        self.card_data = sorted(card_data, key=lambda x: x.hidden_until)
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
        else:
            self.ids['answer'].text = 'No more cards!'
        if self.next_card is not None:
            self.ids['q_next'].text = '(Upcoming: %s)' % self._wrap_question(
                self.next_card.left, self.next_card.left_info)
        # update set statistics:
        self.set_info_label.text = \
            'total selected cards: %i\n' \
            'to learn this session: %i\n' \
            'never seen: %i' % (
                self.total_cards, len(self.card_data),
                len([x for x in self.card_data if x.last_seen == datetime.datetime.min])
            )

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
        if self.current_card is None:
            set_screen_active('manage')
            return
        self.ids['answer'].text = self.current_card.right

    def wrong_answer(self):
        if self.current_card is None:
            set_screen_active('manage')
            return
        self.current_card.streak = 0
        self.storage.update_card_queue.put(self.current_card.card_id)
        self.move_current_card_back()

    def right_answer(self):
        if self.current_card is None:
            set_screen_active('manage')
            return
        self.current_card.streak += 1
        self.current_card.last_seen = datetime.datetime.utcnow()
        self.current_card.hidden_until = datetime.datetime.utcnow() + \
            datetime.timedelta(hours=(12 * 2 ** (self.current_card.streak - 1) - 2))
        self.storage.update_card_queue.put(self.current_card.card_id)
        self.card_data = self.card_data[min(len(self.card_data), 1):]
        self.update_questions()

    def delay_current(self):
        if self.current_card is None:
            set_screen_active('manage')
            return
        self.current_card.hidden_until = datetime.datetime.utcnow() + \
            datetime.timedelta(hours=10)
        self.storage.update_card_queue.put(self.current_card.card_id)
        self.card_data = self.card_data[min(len(self.card_data), 1):]
        self.update_questions()

    def edit_current(self):
        if self.current_card is None:
            set_screen_active('manage')
            return
        EditCardPopup(self.current_card).open()

    def act_on_card_edit(self):
        self.storage.update_card_queue.put(self.current_card.card_id)
        # move card to position 6
        self.move_current_card_back()

    def move_current_card_back(self, steps=6):
        self.card_data.insert(min(steps, len(self.card_data)), self.current_card)
        self.card_data = self.card_data[min(len(self.card_data), 1):]
        self.update_questions()
