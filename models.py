# define database models
from datetime import datetime
import peewee as pw

database = pw.SqliteDatabase("gocards.db")


class BaseModel(pw.Model):
    class Meta:
        database = database


class CardSet(BaseModel):
    """
    ORM model of the Card Sets table
    """
    name = pw.CharField(unique=True)
    description = pw.CharField(default='')
    left_info = pw.CharField(default='')
    right_info = pw.CharField(default='')
    active = pw.BooleanField(default=False)


class Card(BaseModel):
    card_id = pw.AutoField()
    card_set = pw.ForeignKeyField(CardSet, backref='cards')
    left = pw.CharField(default='')
    right = pw.CharField(default='')
    info_left = pw.CharField(default='')
    info_right = pw.CharField(default='')
    last_seen = pw.DateTimeField(default=datetime.min)
    streak = pw.IntegerField(default=0)
    hidden_until = pw.DateTimeField(default=datetime.min)
