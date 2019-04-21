import json
from collections import namedtuple
from datetime import datetime

from ruia import Spider, Item, TextField, Request, Response


class ScriptItem(Item):
    scripts = TextField(css_select='script', many=True)


class Scraper(Spider):
    worker_numbers = 10
    concurrency = 10
    start_urls = ['https://www.instagram.com/explore/tags/cat/']
    posts = []

    async def parse(self, response):
        script = await ScriptItem.get_item(html=response.html)
        yield script

    async def process_item(self, item: ScriptItem):
        shared_data = await self.get_shared_data(item.scripts)

        if shared_data:
            await self.prepare_posts(shared_data)

    async def get_shared_data(self, scripts):
        for script in scripts:
            if 'window._sharedData' in script:
                start = script.find('{')

                if start != -1:  # if found
                    shared_data = json.loads(script[start: len(script) - 1])
                    return shared_data

    async def prepare_posts(self, shared_data):
        url = 'https://www.instagram.com/p/{}/'

        for edge in shared_data['entry_data']['TagPage'][0]['graphql']['hashtag']['edge_hashtag_to_media']['edges']:
            node = edge['node']

            await Request(url=url.format(node['shortcode']), method='GET', callback=self.get_posts).fetch()

    async def get_posts(self, response: Response):
        if 'contentLocation' not in response.html:
            return

        items = await ScriptItem.get_item(html=response.html)

        data = {}

        for script in items.scripts:
            if 'contentLocation' in script:
                data = json.loads(script)
                break

        if data:
            yield Request(
                url=data['contentLocation']['mainEntityofPage']['@id'],
                method='GET',
                callback=self.get_point,
                metadata={'uploadDate': datetime.strptime(data['uploadDate'], '%Y-%m-%dT%H:%M:%S')}
            )

    async def get_point(self, response: Response):
        item = await ScriptItem.get_item(html=response.html)

        shared_data = await self.get_shared_data(item.scripts)

        if not shared_data:
            return

        location = shared_data['entry_data']['LocationsPage'][0]['graphql']['location']

        l = namedtuple('Location', 'lat, lng, name')(location['lat'], location['lng'], location['name'])

        Info = namedtuple('Info', 'location, published_at')

        self.posts.append(
            Info(l, response.metadata['uploadDate'])
        )
