from aiohttp import web
from aiohttp.web_response import json_response

from models.hashtags import Hashtag
from models.posts import Post
from serializers.main import HashtagSerializer, PostSerializer


class TopDistanceView(web.View):
    """
    ---
    description: Top distance method.
    tags:
    - api
    produces:
    - application/json
    parameters:
    - in: path
      name: n
      schema:
        type: integer
        minimum: 1
      required: true
    """

    async def get(self):
        n = self.request.match_info.get('n')

        if not n.isdigit():
            return json_response(
                {'success': False, 'errors': 'n must be int'},
                status=400
            )

        n = int(n)

        db = self.request.app['objects']
        hashtags = await db.execute(
            Hashtag.select().order_by(Hashtag.total_distance.desc()).limit(n)
        )

        data, _ = HashtagSerializer().dump(hashtags, many=True)

        return json_response(data)


class TopHopsView(web.View):
    """
    ---
    description: Top hops method.
    tags:
    - api
    produces:
    - application/json
    parameters:
    - in: path
      name: n
      schema:
        type: integer
        minimum: 1
      required: true
    """

    async def get(self):
        n = self.request.match_info.get('n')

        if not n.isdigit():
            return json_response(
                {'success': False, 'errors': 'n must be int'},
                status=400
            )

        n = int(n)

        db = self.request.app['objects']
        hashtags = await db.execute(
            Hashtag.select().order_by(Hashtag.total_posts.desc()).limit(n)
        )

        data, _ = HashtagSerializer().dump(hashtags, many=True)

        return json_response(data)


class PostsView(web.View):
    """
    ---
    description: Get posts by hashtag method.
    tags:
    - api
    produces:
    - application/json
    parameters:
    - in: path
      name: hashtag
      schema:
        type: string
      required: true
    """

    async def get(self):
        hashtag_name = self.request.match_info.get('hashtag')

        if not hashtag_name:
            return json_response(
                {'success': False, 'errors': 'hashtag is required'},
                status=400
            )

        db = self.request.app['objects']
        posts = await db.execute(
            Post.select().join(Hashtag)
                .where(Hashtag.name == hashtag_name)
        )

        data, _ = PostSerializer().dump(posts, many=True)

        return json_response(data)
