import asyncio
import logging
import os
import time

from aiohttp import web
from aiohttp_swagger import setup_swagger

import updater
from models.base import create_db, close_db
from models.hashtags import Hashtag
from scraper import Scraper
from views import main


async def start_scraper():
    while True:
        tags = await db.execute(
            Hashtag.select()
        )
        scraper = Scraper(
            tags,
            concurrency=os.getenv("concurrency", 200),
            proxy=os.getenv("proxy")
        )
        t1 = time.time()

        asyncio.ensure_future(scraper.parse_all_tags())
        await updater.update_statistics(db, scraper.result_queue)

        logging.info("SCRAPER DONE AT TIME WORK %d", time.time() - t1)


ROUTES = (
    ('GET', r'/top_distance/{n:\d+}', main.TopDistanceView),
    ('GET', r'/top_hops/{n:\d+}', main.TopHopsView),
    ('GET', r'/{hashtag:\w+}', main.PostsView),
)


def get_app(db):
    app = web.Application(client_max_size=0)
    app['objects'] = db

    app.on_cleanup.append(close_db)

    for ROUTE in ROUTES:
        app.router.add_route(*ROUTE)

    setup_swagger(app, swagger_url="/api/docs/")

    return app


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s',
                        level=logging.INFO)

    loop = asyncio.get_event_loop()
    db = create_db()

    future = asyncio.ensure_future(start_scraper())

    app = get_app(db)

    try:
        web.run_app(app, port=8000)
    finally:
        future.cancel()
