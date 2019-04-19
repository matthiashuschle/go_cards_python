import random
import datetime
import threading
from queue import Queue
from collections import OrderedDict
from contextlib import contextmanager
import peewee
from kivy.logger import Logger
from .db_models import CardSet, Card, database  #noqa

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


class CardHolder:

    def __init__(self, card, card_set):
        self.card = card
        self.card_set = card_set

    def to_dict(self):
        return self.card.to_dict()


class Storage:

    def __init__(self):
        self.card_sets = OrderedDict()
        self.cards = OrderedDict
        self.db_lock = threading.Lock()
        with self.db_access():
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
                try:
                    card = self.cards[card_id].card
                except KeyError:
                    continue
                with self.db_access():
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
        self.card_sets = OrderedDict([
            (x.name, x) for x in CardSet
            .select(CardSet, peewee.fn.COUNT(Card.card_id).alias('card_count'))
            .join(Card, peewee.JOIN.LEFT_OUTER)
            .group_by(CardSet)
            .order_by(CardSet.name)
        ])
        self.cards = OrderedDict()
        for card_set in self.card_sets.values():
            for card in Card.select().where(Card.card_set == card_set):
                self.cards[card.card_id] = CardHolder(card, card_set)
        Logger.info('Loaded %i card sets with %i cards' % (len(self.card_sets), len(self.cards)))

    def set_sets_active(self, active_sets):
        with self.db_access():
            for card_set in self.card_sets.values():
                if (card_set.name in active_sets) != card_set.active:
                    card_set.active = card_set.name in active_sets
                    card_set.save()

    def add_new_set(self, value_dict):
        with self.db_access():
            new_set = CardSet(**value_dict)
            new_set.save()
            self.refresh_data()
            return new_set

    def add_new_card(self, value_dict, card_set):
        print('add new card')
        print(card_set)
        with self.db_access():
            new_card = Card(card_set=card_set, **value_dict)
            new_card.save()
            self.refresh_data()

    def update_set(self, cardset_id):
        with self.db_access():
            # may change a set's name!
            old_name, cardset = None, None
            found = False
            for old_name, cardset in self.card_sets.items():
                if cardset.cardset_id == cardset_id:
                    found = True
                    cardset.save()
                    break
            if found and cardset.name != old_name:
                # rename key in self.card_sets
                self.card_sets = OrderedDict([
                    (cardset.name, cardset) for cardset in self.card_sets.values()
                ])

    def add_many_cards(self, value_dicts, card_set):
        with self.db_access():
            for value_dict in value_dicts:
                new_card = Card(card_set=card_set, **value_dict)
                new_card.save()
            self.refresh_data()

    def copy_set_to(self, old_set, new_name, shuffle=False, swap=False, reset=False,
                    apply_qi=False, apply_ai=False):
        new_set_probs = {
            'name': new_name,
            'description': old_set.description,
            'left_info': old_set.left_info if not swap else old_set.right_info,
            'right_info': old_set.right_info if not swap else old_set.left_info
        }
        # create cards as value dictionaries
        cards = []
        for card in self.cards.values():
            if card.card_set != old_set:
                continue
            card_dict = card.to_dict()
            del card_dict['card_id']
            if apply_qi:
                card_dict['left_info'] = old_set.left_info
            if apply_ai:
                card_dict['right_info'] = old_set.right_info
            if swap:
                card_dict['left'], card_dict['right'] = card_dict['right'], card_dict['left']
                card_dict['left_info'], card_dict['right_info'] = card_dict['right_info'], card_dict['left_info']
            if reset:
                del card_dict['hidden_until']
                del card_dict['last_seen']
                del card_dict['streak']
            cards.append(card_dict)
        if shuffle:
            random.shuffle(cards)
        with self.db_access():
            new_set = CardSet(**new_set_probs)
            new_set.save()
        self.add_many_cards(cards, new_set)

    def delete_set(self, cardset):
        with self.db_access():
            cardset.delete_instance(recursive=True)
            self.refresh_data()

    def delete_card(self, card):
        with self.db_access():
            card.delete_instance()
            self.refresh_data()

    def merge_sets(self, selected_set_names, set_name):
        new_set_probs = {'name': set_name}
        # create cards as value dictionaries
        cards = []
        for card in self.cards.values():
            if card.card_set.name not in selected_set_names:
                continue
            card_dict = card.to_dict()
            del card_dict['card_id']
            cards.append(card_dict)
        with self.db_access():
            new_set = CardSet(**new_set_probs)
            new_set.save()
        self.add_many_cards(cards, new_set)
