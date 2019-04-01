import peewee
from contextlib import contextmanager
from kivy.logger import Logger
from db_models import CardSet, Card, database, MIN_DATE
import threading
from queue import Queue
import datetime

DT_FORMAT = '%Y-%m-%d %H:%M:%S'
CARD_TO_STRING = {
    'last_seen': lambda x: x.strftime(DT_FORMAT),
    'hidden_until': lambda x: x.strftime(DT_FORMAT),
}
CARD_FROM_STRING = {
    'last_seen': lambda x: datetime.datetime.strptime(x, DT_FORMAT),
    'hidden_until': lambda x: datetime.datetime.strptime(x, DT_FORMAT),
    'streak': int
}
CARDSET_TO_STRING = {}
CARDSET_FROM_STRING = {}


class Storage:

    def __init__(self):
        self.card_sets = None
        self.cards = None
        self.db_lock = threading.Lock()
        with self.db_lock:
            self.create_tables()
            self.refresh_data()
        self.update_card_queue = Queue()
        self.update_thread = threading.Thread(target=self.update_card_loop, daemon=True)
        self.update_thread.start()

    @contextmanager
    def db_access(self):
        with self.db_lock:
            with database:
                yield

    def update_card_loop(self):
        while True:
            card_id = self.update_card_queue.get()
            if card_id is not None:
                card = [x for x in self.cards if x.card_id == card_id]
                if len(card) != 1:
                    continue
                card = card[0]
                with self.db_lock:
                    card.save()

    @staticmethod
    def create_tables():
        database.create_tables([CardSet, Card], safe=True)
        n_entries = CardSet.select(CardSet.name).count()
        Logger.info('database has %i card sets' % n_entries)
        if not n_entries:
            test_set = CardSet(name='test_set', left_info='DE', right_info='EN')
            test_set.save()
            test_card = Card(card_set=test_set, left='hallo', right='hello', left_info='DE', right_info='EN')
            test_card.save()
            test_card = Card(card_set=test_set, left='hallo 2', right='hello 2', left_info='DE', right_info='EN')
            test_card.save()

    def refresh_data(self):
        self.card_sets = [
            x for x in CardSet
                .select(CardSet, peewee.fn.COUNT(Card.card_id).alias('card_count'))
                .join(Card, peewee.JOIN.LEFT_OUTER)  # include people without pets.
                .group_by(CardSet)
                .order_by(CardSet.name)
        ]
        self.cards = [x for x in Card.select(Card)]
        Logger.info('Loaded %i card sets' % len(self.card_sets))

    def set_sets_active(self, active_sets):
        for card_set in self.card_sets:
            if (card_set.name in active_sets) != card_set.active:
                card_set.active = card_set.name in active_sets
                card_set.save()

    def add_new_set(self, value_dict):
        with self.db_lock:
            new_set = CardSet(**value_dict)
            new_set.save()
            self.refresh_data()

    def add_new_card(self, value_dict, card_set):
        with self.db_lock:
            new_card = Card(card_set=card_set, **value_dict)
            new_card.save()
            self.refresh_data()

    def update_set(self, cardset_id):
        with self.db_lock:
            cardset = [x for x in self.card_sets if x.cardset_id == cardset_id]
            if len(cardset) != 1:
                return
            cardset = cardset[0]
            cardset.save()
