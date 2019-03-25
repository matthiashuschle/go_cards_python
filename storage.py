from models import CardSet, Card, database


def create_tables():
    database.connect()
    database.create_tables([CardSet, Card], safe=True)
    database.close()


