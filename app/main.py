import asyncio
import json
import logging
import time

from aiohttp import web

from scraper import Scraper


async def get_app():
    app = web.Application(client_max_size=0)

    return app


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s',
                        level=logging.INFO)

    loop = asyncio.get_event_loop()

    tags = open('words.txt', 'r').read().split('\n')

    scraper = Scraper(tags, concurrency=100, proxy="http://172.19.0.1:8080")
    t1 = time.time()
    loop.run_until_complete(scraper.parse_all_tags())
    print(len(scraper.posts))

    print("TIME WORK", time.time() - t1)

    with open('all.txt', 'w') as f:
        f.write(json.dumps([p._asdict() for p in scraper.posts], default=str))

    # app = loop.run_until_complete(get_app())
    #
    # web.run_app(app, port=8000)
