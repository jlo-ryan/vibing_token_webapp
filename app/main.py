import asyncio
import logging
import time

from aiohttp import web

import updater
from models.base import create_db
from models.hashtags import Hashtag
from scraper import Scraper


async def get_app():
    app = web.Application(client_max_size=0)

    return app


async def main():
    db = create_db()
    tags = await db.execute(
        Hashtag.select(),
    )

    scraper = Scraper(tags, concurrency=100)  # , proxy="http://172.19.0.1:8080")
    t1 = time.time()
    await scraper.parse_all_tags()

    await updater.update_statistics(db, scraper.posts)

    logging.info("TIME WORK %d", time.time() - t1)

    # app = loop.run_until_complete(get_app())
    #
    # web.run_app(app, port=8000)


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s',
                        level=logging.DEBUG)

    loop = asyncio.get_event_loop()

    app = loop.run_until_complete(main())
