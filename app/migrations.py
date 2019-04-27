import logging

import peewee

from models.base import database
from models.hashtags import Hashtag
from models.posts import Post

logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s',
                    level=logging.INFO)

logger = logging.getLogger()

logger.info('INIT DB')
objects = peewee.PostgresqlDatabase(database)

logger.info('START CREATE TABLES')
Hashtag.create_table(safe=True)
Post.create_table(safe=True)
logger.info('END CREATE TABLES')
