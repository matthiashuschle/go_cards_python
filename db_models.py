# define database models
from datetime import datetime
import peewee as pw

database = pw.SqliteDatabase("gocards.db")
MIN_DATE = datetime(1999, 12, 31)


class BaseModel(pw.Model):
    class Meta:
        database = database


class CardSet(BaseModel):
    """
    ORM model of the Card Sets table
    """
    cardset_id = pw.AutoField()
    name = pw.CharField(unique=True)
    description = pw.CharField(default='')
    left_info = pw.CharField(default='')
    right_info = pw.CharField(default='')
    active = pw.BooleanField(default=False)

    def to_dict(self):
        return {
            'cardset_id': self.cardset_id,
            'name': self.name,
            'description': self.description,
            'left_info': self.left_info,
            'right_info': self.right_info,
            'active': self.active,
        }


class Card(BaseModel):
    card_id = pw.AutoField()
    card_set = pw.ForeignKeyField(CardSet, backref='cards')
    left = pw.CharField(default='')
    right = pw.CharField(default='')
    left_info = pw.CharField(default='')
    right_info = pw.CharField(default='')
    last_seen = pw.DateTimeField(default=MIN_DATE)
    streak = pw.IntegerField(default=0)
    hidden_until = pw.DateTimeField(default=MIN_DATE)

    def to_dict(self):
        return {
            'card_id': self.card_id,
            'left': self.left,
            'right': self.right,
            'left_info': self.left_info,
            'right_info': self.right_info,
            'last_seen': self.last_seen,
            'streak': self.streak,
            'hidden_until': self.hidden_until,
        }
