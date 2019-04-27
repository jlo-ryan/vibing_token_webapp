from postgis import Point

from models.hashtags import Hashtag
from models.posts import Post


async def update_statistics(db, posts):
    posts.sort(key=lambda x: x.published_at)

    for post in posts:
        hashtag = await db.get(Hashtag, name=post.tag)

        posts_db = list(await db.execute(
            Post.select(Post, Hashtag)
                .join(Hashtag)
                .where(Hashtag.name == post.tag)
                .order_by(Post.published_at)
        ))

        dates = [i.published_at for i in posts_db]

        newest = True

        if dates:
            newest = post.published_at > max(dates)

        if newest:
            point = Point(post.location.lat, post.location.lng, srid=4326)
            data = {
                'hashtag_id': hashtag.id,
                'published_at': post.published_at,
                'url': post.url,
                'location': post.location.name,
                'point': point
            }
            await db.create(Post, **data)

            if not posts_db:
                continue

            hashtag.total_posts += 1

            total_distance = hashtag.total_distance

            last_point_in_db = posts_db[0].point

            distance_between_last_points = await db.execute(Post.raw("""
            SELECT ST_Distance(
                    'SRID=4326;POINT(%s %s)'::geography,
                    'SRID=4326;POINT(%s %s)'::geography
            )/1000 as distance
            """, *point.coords, *last_point_in_db.coords))

            distance_between_last_points = distance_between_last_points[0].distance
            hashtag.total_distance = total_distance + distance_between_last_points

            await db.update(hashtag)

