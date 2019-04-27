import peewee

from models.base import BaseModel


class Hashtag(BaseModel):
    name = peewee.TextField()
    number = peewee.IntegerField()
    total_posts = peewee.IntegerField(default=0)
    total_distance = peewee.IntegerField(default=0)

    class Meta:
        table_name = 'hashtags'
