import peewee
from contextlib import contextmanager
from kivy.logger import Logger
from db_models import CardSet, Card, database
import threading
from queue import Queue, Empty


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

    def add_new_set(self, name, description, left_info, right_info):
        with self.db_lock:
            new_set = CardSet(name=name, description=description,
                              left_info=left_info, right_info=right_info)
            new_set.save()
            self.refresh_data()
