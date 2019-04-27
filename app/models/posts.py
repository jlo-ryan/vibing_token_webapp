import peewee

from models.base import BaseModel
from models.base import PointField
from models.hashtags import Hashtag


class Post(BaseModel):
    hashtag = peewee.ForeignKeyField(Hashtag, backref='posts')

    published_at = peewee.DateTimeField()
    url = peewee.TextField()
    location = peewee.TextField(null=True)
    point = PointField(null=True)

    class Meta:
        table_name = 'posts'
        order_by = ['published_at']
