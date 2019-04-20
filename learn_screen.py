import os
import datetime
from kivy.uix.screenmanager import Screen
from kivy.logger import Logger
from kivy.properties import ObjectProperty
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.recycleview import RecycleView
from storage import MIN_DATE, DT_FORMAT
from common import set_screen_active, get_screen, CardPopup, DeletePopup, hide_widget
from debug import log_time


class LearnBatchLabel(RecycleDataViewBehavior, BoxLayout):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.question = None
        self.answer = None
        self.card_id = None
        self.correct = False
        self.index = None
        self.revealed = False

    def refresh_view_attrs(self, rv, index, data):
        """ Catch and handle the view changes """
        # self.index = index
        self.correct = False
        self.revealed = False
        self.card_id = data['card_id']
        self.question = data['question']
        self.answer = data['answer']
        self.index = index
        btn_left = self.ids['btn_left']
        btn_right = self.ids['btn_right']
        btn_left.text = self.question
        btn_right.text = '<reveal!>'
        self._set_bg_color()
        return super(LearnBatchLabel, self).refresh_view_attrs(
            rv, index, data)

    def _set_bg_color(self):
        color = [0., 0., 0., 1.]
        if self.index % 2 == 0:
            color = [0.1, 0.1, 0.1, 1.]
        if self.correct:
            color = [0.29, 0.569, 0.188, 1]
        self.ids['btn_left'].background_color = color
        self.ids['btn_right'].background_color = color

    def set_correct(self):
        self.correct = not self.correct
        self._set_bg_color()

    def reveal(self):
        if not self.revealed:
            self.ids['btn_right'].text = self.answer
            self.revealed = True
        else:
            self.set_correct()
        # self.ids['btn_right'].disabled = True


class LearnBatchRV(RecycleView):

    def __init__(self, **kwargs):
        super(LearnBatchRV, self).__init__(**kwargs)
        Logger.info('in RV')

    def get_results(self):
        return {self.data[ix]['card_id']: node.correct for node, ix in
                self.ids['rv_layout'].view_indices.items()}


class EditCardPopup(CardPopup):

    def cancel(self):
        get_screen('learn').move_current_card_back()
        self.dismiss()

    def act_on_save(self, value_dict):
        for field, value in value_dict.items():
            setattr(self.db_object, field, value)
        get_screen('learn').act_on_card_edit()

    def delete(self):
        DeletePopup(self.db_object.left, callback=self.act_on_delete).open()

    def act_on_delete(self):
        get_screen('learn').act_on_card_delete(self.db_object)
        self.dismiss()


class LearnScreen(Screen):

    set_info_label = ObjectProperty(None)
    learn_layout = ObjectProperty(None)
    layout_single = ObjectProperty(None)
    layout_batch = ObjectProperty(None)
    box_batch_table = ObjectProperty(None)
    selected_sets = []
    BATCH_LEN = 10

    def __init__(self, storage, **kwargs):
        super().__init__(**kwargs)
        self.storage = storage
        self.card_data = []
        self.total_cards = 0
        self.batch_mode = False
        self.rv = LearnBatchRV()
        self.box_batch_table.add_widget(self.rv)
        hide_widget(self.layout_batch, True)
        Logger.info('in LearnScreen')

    def update_cards(self, selected_sets):
        with log_time('learn - set_sets_active'):
            self.storage.set_sets_active(selected_sets)
        with log_time('learn - select cards'):
            card_data = [x.card for x in self.storage.cards.values() if x.card_set.name in selected_sets]
        with log_time('learn - prepare cards'):
            self.total_cards = len(card_data)
            now = datetime.datetime.utcnow()
            card_data = [x for x in card_data if x.hidden_until < now]
            # unseen cards are shown last! Repeat seen cards first for better learning effect on large sets
            seen = [x for x in card_data if x.hidden_until > MIN_DATE]
            unseen = [x for x in card_data if x.hidden_until == MIN_DATE]
            self.card_data = sorted(seen, key=lambda x: x.hidden_until) + unseen
        with log_time('learn - update questions'):
            self.update_questions()
        with log_time('learn - update batch questions'):
            self.update_batch_questions()

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
        self.set_info_label.text = os.linesep.join([
            'total selected cards: %i' % self.total_cards,
            'to learn this session: %i' % len(self.card_data),
            'never seen: %i' % len([x for x in self.card_data if x.last_seen == MIN_DATE])
        ])

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

    def _modify_card_on_wrong(self, card):
        card.streak = 0
        self.storage.update_card_queue.put(card.card_id)

    def wrong_answer(self):
        if self.current_card is None:
            set_screen_active('manage')
            return
        self._modify_card_on_wrong(self.current_card)
        self.move_current_card_back()

    def _modify_card_on_right(self, card):
        card.streak += 1
        card.last_seen = datetime_cut_ms(datetime.datetime.utcnow())
        card.hidden_until = datetime_cut_ms(
            datetime.datetime.utcnow() + datetime.timedelta(hours=(12 * 2 ** (card.streak - 1) - 2)))
        self.storage.update_card_queue.put(card.card_id)

    def right_answer(self):
        if self.current_card is None:
            set_screen_active('manage')
            return
        self._modify_card_on_right(self.current_card)
        self.card_data = self.card_data[min(len(self.card_data), 1):]
        self.update_questions()

    def delay_current(self):
        if self.current_card is None:
            set_screen_active('manage')
            return
        self.current_card.hidden_until = datetime_cut_ms(
            datetime.datetime.utcnow() + datetime.timedelta(hours=10))
        self.storage.update_card_queue.put(self.current_card.card_id)
        self.card_data = self.card_data[min(len(self.card_data), 1):]
        self.update_questions()

    def edit_current(self):
        if self.current_card is None:
            set_screen_active('manage')
            return
        EditCardPopup('Edit Card', db_object=self.current_card).open()

    def act_on_card_edit(self):
        self.storage.update_card_queue.put(self.current_card.card_id)
        # move card to position 6
        self.move_current_card_back()

    def move_current_card_back(self, steps=6):
        self.card_data.insert(min(steps, len(self.card_data)), self.current_card)
        self.card_data = self.card_data[min(len(self.card_data), 1):]
        self.update_questions()

    def act_on_card_delete(self, card):
        self.storage.delete_card(card)
        self.card_data = self.card_data[1:]
        self.update_questions()

    def activate_single(self):
        self.update_questions()
        hide_widget(self.layout_batch, True)
        hide_widget(self.layout_single, False)

    def activate_batch(self):
        self.update_batch_questions()
        hide_widget(self.layout_single, True)
        hide_widget(self.layout_batch, False)

    # Batch Mode
    def switch_mode(self):
        if self.batch_mode:
            self.activate_single()
            self.batch_mode = False
        elif len(self.card_data):
            self.activate_batch()
            self.batch_mode = True

    def update_batch_questions(self):
        if self.current_card is None:
            self.activate_single()
            return
        self.rv.data = [{
            'card_id': card.card_id,
            'question': card.left,
            'answer': card.right
        } for card in self.card_data[:self.BATCH_LEN]]

    def submit_batch(self):
        results = self.rv.get_results()
        seen = set()
        shelved = []
        while len(self.card_data) and self.card_data[0].card_id in results:
            card_id = self.current_card.card_id
            if card_id in seen:
                # We arrive here if an early card is moved back.
                # We want to avoid processing those repeatedly.
                # So we remove them temporarily and insert them after processing the whole batch.
                shelved.append(self.current_card)
                self.card_data = self.card_data[1:]
                continue
            correct = results[card_id]
            if correct:
                self.right_answer()
            else:
                self.wrong_answer()
            seen.add(card_id)
        if len(shelved):
            self.card_data = shelved + self.card_data
            self.update_questions()
        self.update_batch_questions()


def datetime_cut_ms(dt):
    return datetime.datetime.strptime(dt.strftime(DT_FORMAT), DT_FORMAT)
