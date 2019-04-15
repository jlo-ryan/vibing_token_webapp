import peewee

from models.base import BaseModel
from models.hashtags import Hashtag


class Post(BaseModel):
    hashtag = peewee.ForeignKeyField(Hashtag)

    published_at = peewee.DateTimeField()
    url = peewee.TextField()
    location = peewee.TextField(null=True)

    class Meta:
        table_name = 'posts'
