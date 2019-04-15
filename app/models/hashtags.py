import peewee

from models.base import BaseModel


class Hashtag(BaseModel):
    name = peewee.TextField()
    number = peewee.IntegerField()

    class Meta:
        table_name = 'hashtags'


class HashtagStatistic(BaseModel):
    total_posts = peewee.IntegerField(default=0)
    total_distance = peewee.IntegerField(default=0)

    class Meta:
        table_name = 'hashtag_statistics'
