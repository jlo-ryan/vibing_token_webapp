import re

import peewee
import peewee_async
from playhouse import postgres_ext
from postgis import Point
import postgis


peewee.OP.update(
    BBOX2D='&&',
    BBOXCONTAINS='~',
    BBOXCONTAINED='@',
)

db_config = {
    'database': 'vibing',
    'user': 'vibing',
    'password': 'ghbdtn',
    'host': 'db',
    'field_types': {'point': 'geometry(Point)'},
    'operations': {
        peewee.OP.BBOX2D: peewee.OP.BBOX2D,
        peewee.OP.BBOXCONTAINS: peewee.OP.BBOXCONTAINS,
        peewee.OP.BBOXCONTAINED: peewee.OP.BBOXCONTAINED,
    }
}

database = peewee_async.PooledPostgresqlDatabase(**db_config)


def create_db():
    database.set_allow_sync(False)
    return peewee_async.Manager(database)


async def close_db(app):
    await database.close()


class BaseModel(peewee.Model):
    class Meta:
        database = database


lonlat_pattern = re.compile('^[\[\(]{1}(?P<lon>-?\d{,3}(:?\.\d*)?), ?(?P<lat>-?\d{,3}(\.\d*)?)[\]\)]{1}$')  # noqa


class PointField(peewee.Field, postgres_ext.IndexedFieldMixin):
    field_type = 'point'
    __data_type__ = Point
    __schema_type__ = 'object'
    __schema_format__ = 'geojson'
    srid = 4326
    index_type = 'GiST'

    def db_value(self, value):
        return self.coerce(value)

    def python_value(self, value):
        return self.coerce(postgis.Point.from_ewkb(value))

    def coerce(self, value):
        if not value:
            return None
        if isinstance(value, Point):
            return value
        if isinstance(value, dict):  # GeoJSON
            value = value['coordinates']
        if isinstance(value, str):
            search = lonlat_pattern.search(value)
            if search:
                value = (float(search.group('lon')),
                         float(search.group('lat')))
            else:
                if not value[0].isdigit() or not value[1].isdigit():
                    raise ValueError
        return Point(value[0], value[1], srid=self.srid)
