import asyncio
import json
import logging
import random
from collections import namedtuple
from datetime import datetime

import aiohttp
from aiohttp import ClientPayloadError
from pyquery import PyQuery as pq


class Scraper:
    start_urls = []
    posts = []
    concurrency = 10
    headers = {}
    proxy = None

    def __init__(self, tags: [list, tuple], concurrency=None, headers=None, proxy=None):
        self.start_urls.extend([('https://www.instagram.com/explore/tags/{}/'.format(i), i) for i in tags])

        if concurrency:
            self.concurrency = concurrency

        if headers:
            self.headers = headers

        if proxy:
            self.proxy = proxy

        self.sem = asyncio.Semaphore(self.concurrency)

    async def fetch(self, url, count_retry=0):
        if count_retry > 3:
            return

        try:
            async with self.sem:
                async with aiohttp.ClientSession() as session:
                    await asyncio.sleep(random.randint(1, 4))

                    logging.info('start request for: %s', url)

                    async with session.get(url, headers=self.headers, proxy=self.proxy) as resp:
                        return await resp.text()
        except ClientPayloadError:
            logging.info("retry fetch: %s, count: %d", url, count_retry)

            return await self.fetch(url, count_retry + 1)

    def get_shared_data(self, scripts):
        for script in scripts:
            text = script.text
            if text is not None and 'window._sharedData = {' in text:
                start = text.find('{')

                if start != -1:  # if found
                    shared_data = json.loads(text[start: len(text) - 1])
                    return shared_data

    async def parse_all_tags(self):
        tasks = []
        for u, t in self.start_urls:
            tasks.append(self.process_item(u, t))

        await asyncio.gather(*tasks)

    def get_scripts(self, html):
        if not html:
            return

        dom = pq(html)
        return dom('script')

    async def process_item(self, url, tag):
        scripts = self.get_scripts(await self.fetch(url))

        if not scripts:
            return

        shared_data = self.get_shared_data(scripts)

        if shared_data:
            await self.prepare_posts(shared_data, tag)

    async def prepare_posts(self, shared_data, tag):
        url = 'https://www.instagram.com/p/{}/'

        tasks = []

        for edge in shared_data['entry_data']['TagPage'][0]['graphql']['hashtag']['edge_hashtag_to_media']['edges']:
            node = edge['node']

            tasks.append(self.get_posts(url.format(node['shortcode']), tag))

        await asyncio.gather(*tasks)

    async def get_posts(self, url, tag):
        response = await self.fetch(url)

        if response is None:
            return

        if 'contentLocation' not in response:
            return

        scripts = self.get_scripts(await self.fetch(url))

        if not scripts:
            return

        data = {}

        for script in scripts:
            if 'contentLocation' in script.text:
                data = json.loads(script.text)
                break

        if data:
            await self.get_point(
                data['contentLocation']['mainEntityofPage']['@id'],
                datetime.strptime(data['uploadDate'], '%Y-%m-%dT%H:%M:%S'),
                data['mainEntityofPage']['@id'], tag
            )

    async def get_point(self, url, upload_time, post_url, tag):
        scripts = self.get_scripts(await self.fetch(url))
        if not scripts:
            return

        shared_data = self.get_shared_data(scripts)

        if not shared_data:
            return

        location = shared_data['entry_data']['LocationsPage'][0]['graphql']['location']

        l = namedtuple('Location', 'lat, lng, name')(location['lat'], location['lng'], location['name'])

        Info = namedtuple('Info', 'location, published_at, url, tag')

        self.posts.append(Info(l, upload_time, post_url, tag))
