import peewee

from models.base import BaseModel


class Hashtag(BaseModel):
    name = peewee.TextField()
    number = peewee.IntegerField()

    class Meta:
        table_name = 'hashtags'
