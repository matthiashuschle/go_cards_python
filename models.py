# define database models
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
    description = pw.CharField()
    left_info = pw.CharField()
    right_info = pw.CharField()
    active = pw.BooleanField()


class Card(BaseModel):
    card_id = pw.AutoField()
    card_set = pw.ForeignKeyField(CardSet, backref='cards')
    left = pw.CharField()
    right = pw.CharField()
    info_left = pw.CharField()
    info_right = pw.CharField()
    last_seen = pw.DateTimeField()
    streak = pw.IntegerField()
    hidden_until = pw.DateTimeField()
