import peewee
import peewee_async

db_config = {
    'database': 'vibing',
    'user': 'vibing',
    'password': 'ghbdtn',
    'host': 'db'
}

database = peewee_async.PooledPostgresqlDatabase(**db_config)


def create_db():
    database.set_allow_sync(False)
    return peewee_async.Manager(database)


class BaseModel(peewee.Model):
    class Meta:
        database = database
