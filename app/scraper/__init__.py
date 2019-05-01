import asyncio
import json
import logging
from asyncio import QueueEmpty
from collections import namedtuple
from datetime import datetime

import aiohttp
from aiohttp import ClientPayloadError, ClientConnectorError, ClientOSError, ServerDisconnectedError
from pyquery import PyQuery as pq


class Scraper:
    concurrency = 10
    workers = 5
    headers = {
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'}
    proxy = None
    queue = asyncio.Queue()
    result_queue = asyncio.Queue()

    def __init__(self, tags, concurrency=None, headers=None, proxy=None):
        self.start_urls = (('https://www.instagram.com/explore/tags/{}/'.format(i.name), i.name) for i in tags)

        if concurrency:
            self.concurrency = concurrency

        if headers:
            self.headers = headers

        if proxy:
            self.proxy = proxy

        self.sem = asyncio.Semaphore(self.concurrency)

    async def fetch(self, url, tag, count_retry=0):
        if count_retry > 4:
            logging.info("[fetch] exit")
            self.queue.put_nowait((url, tag))
            return

        try:
            async with self.sem:
                async with aiohttp.ClientSession(
                        timeout=aiohttp.ClientTimeout(total=30),
                        connector=aiohttp.TCPConnector(verify_ssl=False)) as session:
                    logging.info('start request for: %s', url)

                    async with session.get(url, headers=self.headers, proxy=self.proxy) as resp:
                        if resp.status == 200:
                            return await resp.text()

                        if resp.status != 429:
                            return

        except ClientPayloadError:
            logging.info("[ClientPayloadError] retry fetch: %s, count: %d", url, count_retry)
        except ClientConnectorError:
            logging.info("[ClientConnectorError] retry fetch: %s, count: %d", url, count_retry)
        except ClientOSError:
            logging.info("[ClientOSError] retry fetch: %s, count: %d", url, count_retry)
        except asyncio.TimeoutError:
            logging.info("[TimeoutError] retry fetch: %s, count: %d", url, count_retry)
        except ServerDisconnectedError:
            logging.info("[ServerDisconnectedError] retry fetch: %s, count: %d", url, count_retry)
        except Exception as e:
            logging.info("[Unknown exception] %s", str(e))
            return

        logging.info("[last] retry fetch: %s, count: %d", url, count_retry)
        return await self.fetch(url, tag, count_retry=count_retry + 1)

    def get_shared_data(self, scripts):
        for script in scripts:
            text = script.text
            if text is not None and 'window._sharedData = {' in text:
                start = text.find('{')

                if start != -1:  # if found
                    shared_data = json.loads(text[start: len(text) - 1])
                    return shared_data

    def get_scripts(self, html):
        if not html:
            return

        dom = pq(html)
        return dom('script')

    def fill_queue(self):
        for u, t in self.start_urls:
            self.queue.put_nowait((u, t))

    async def parse_all_tags(self):
        self.fill_queue()

        workers = []

        for _ in range(self.workers):
            workers.append(self.worker())

        await asyncio.gather(*workers)

        await asyncio.sleep(1)  # small delay before exit
        self.result_queue.put_nowait(None)  # send stop signal

    async def worker(self):
        while True:
            try:
                item = self.queue.get_nowait()
            except QueueEmpty:
                return

            try:
                await self.process_item(*item)
            finally:
                self.queue.put_nowait(item)

                self.queue.task_done()

    async def process_item(self, url, tag):
        scripts = self.get_scripts(await self.fetch(url, tag))

        if not scripts:
            logging.info('process_item not scripts')
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
        response = await self.fetch(url, tag)

        if response is None:
            logging.info('get_posts response is None')

            return

        if 'contentLocation' not in response:
            return

        scripts = self.get_scripts(await self.fetch(url, tag))

        if not scripts:
            logging.info('get_posts not scripts')

            return

        data = {}

        for script in scripts:
            if script.text is not None and 'contentLocation' in script.text:
                data = json.loads(script.text)
                break

        if data:
            await self.get_point(
                data['contentLocation']['mainEntityofPage']['@id'],
                datetime.strptime(data['uploadDate'], '%Y-%m-%dT%H:%M:%S'),
                data['mainEntityofPage']['@id'], tag
            )

    async def get_point(self, url, upload_time, post_url, tag):
        scripts = self.get_scripts(await self.fetch(url, tag))
        if not scripts:
            logging.info('get_point not scripts')

            return

        shared_data = self.get_shared_data(scripts)

        if not shared_data:
            logging.info('get_point not shared_data')

            return

        location = shared_data['entry_data']['LocationsPage'][0]['graphql']['location']

        l = namedtuple('Location', 'lat, lng, name')(location['lat'], location['lng'], location['name'])

        Info = namedtuple('Info', 'location, published_at, url, tag')

        i = Info(l, upload_time, post_url, tag)
        self.result_queue.put_nowait(i)
