import asyncio
import logging

from aiohttp import web

from scraper import Scraper


async def get_app():
    app = web.Application(client_max_size=0)

    return app


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s',
                        level=logging.INFO)

    loop = asyncio.get_event_loop()
    scraper = Scraper.start(loop=loop)
    print(scraper)
    # app = loop.run_until_complete(get_app())
    #
    # web.run_app(app, port=8000)
