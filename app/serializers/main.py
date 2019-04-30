from marshmallow import Schema, fields


class HashtagSerializer(Schema):
    id = fields.Int()
    name = fields.Str()
    total_distance = fields.Int()
    total_posts = fields.Int()


class PostSerializer(Schema):
    id = fields.Int()
    hashtag_id = fields.Int()
    published_at = fields.DateTime()
    url = fields.Str()
    location = fields.Str(required=False, allow_none=True)
