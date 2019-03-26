import peewee
from kivy.logger import Logger
from models import CardSet, Card, database


class Storage:

    def __init__(self):
        self.card_sets = None
        self.cards = None
        with database:
            self.create_tables()
            self.refresh_data()

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
            Card.insert(test_card)

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
