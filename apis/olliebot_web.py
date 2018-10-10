import aiohttp

from util.feeds import *
from util.exceptions import *


class RssApiError(Exception):
    pass


class BotApiError(Exception):
    pass


class OllieBotAPI:
    """Accesses features of bot.olliebot.cc

    """

    BOT_API = "https://bot.olliebot.cc/"
    RSS_API = "https://rss.olliebot.cc/"

    def __init__(self, token):
        self.token = token

    async def get_eight_ball(self, fn: str = None) -> str:
        """Returns a random eight ball image

        Parameters
        ----------
        fn : str
            a specific filename to retrieve. returns random if 'None'

        Returns
        -------
        str
            url of file

        """

        if fn:
            url = self._build_url(self.BOT_API, 'eb', img=fn)
        else:
            url = self._build_url(self.BOT_API, 'eb')

        resp = await self._get_json(url)

        if resp:
            return resp['url']

    async def create_twitter_feed(self, handle: str) -> TwitterFeed:
        """Creates a twitter feed

        Parameters
        ----------
        handle : str
            the twitter handle

        Returns
        -------
        :class:`TwitterFeed`
            the new feed

        Raises
        ------
        :class:`util.exceptions.HTTPBadRequest`
            indicates the api was used incorrectly
        :class:`RssApiError`
            indicates the feed creation failed
        """
        print('initiating twitter request')

        url = self._build_url(api=self.RSS_API, endpoint='create')

        resp = await self._single_post_request(url, json={'type': 'twitter', 'handle': handle})

        if resp.status == 200:
            raw_feed = await resp.json()
            return TwitterFeed(**raw_feed)
        elif resp.status == 400:
            raise HTTPBadRequest('Twitter feed request error')
        else:
            raise RssApiError('Could not create feed for given handle')

    async def create_twitch_feed(self, username: str) -> TwitchFeed:
        """Creates a twitch feed

        Parameters
        ----------
        username : str
            the twitch channel username

        Returns
        -------
        :class:`TwitchFeed`
            the new feed

        Raises
        ------
        :class:`util.exceptions.HTTPBadRequest`
            indicates the api was used incorrectly
        :class:`RssApiError`
            indicates the feed creation failed
        """

        url = self._build_url(api=self.RSS_API, endpoint='create')

        resp = await self._single_post_request(url, json={'type': 'twitch', 'username': username})

        if resp.status == 200:
            raw_feed = await resp.json()
            return TwitchFeed(**raw_feed)
        elif resp.status == 400:
            raise HTTPBadRequest('Twitch feed request error')
        else:
            raise RssApiError('Could not create feed for given channel')

    async def create_youtube_feed(self, username: str = None, id: str = None) -> YouTubeFeed:
        """Creates a youtube feed

        Parameters
        ----------
        username : str
            the youtube channel username
        id : str
            the youtube channel id

        Returns
        -------
        :class:`YouTubeFeed`
            the new feed

        Raises
        ------
        :class:`util.exceptions.HTTPBadRequest`
            indicates the api was used incorrectly
        :class:`RssApiError`
            indicates the feed creation failed
        """

        url = self._build_url(api=self.RSS_API, endpoint='create')
        json_data = self._build_json(type='youtube', username=username, id=id)

        resp = await self._single_post_request(url, json=json_data)

        if resp.status == 200:
            raw_feed = await resp.json()
            return YouTubeFeed(**raw_feed)
        elif resp.status == 400:
            raise HTTPBadRequest('Youtube feed request error')
        else:
            raise RssApiError('Could not create feed for given channel')

    async def get_feed(self, *, id: str = None, name: str = None) -> RssFeed:
        """Retrieves a feed, either by its feed.id attribute or
        by a name (handle or username)

        Parameters
        ----------
        id : str
            the :class:`RssFeed` id to retrieve
        name : str
            the username associated with the feed

        Returns
        -------
        :class:`RssFeed`
            the found feed

        Raises
        ------
        :class:`util.exceptions.HTTPBadRequest`
            indicates the api was used incorrectly
        :class:`RssApiError`
            indicates the feed retrieval failed
        """

        url = self._build_url(api=self.RSS_API, endpoint='retrieve', id=id, name=name)

        resp = await self._single_get_request(url)

        if resp.status == 200:
            raw_feed = await resp.json()
            return self.build_feed(raw_feed)
        elif resp.status == 400:
            raise HTTPBadRequest('Feed request error')
        else:
            raise RssApiError('Could not retrieve feed for given channel')

    async def get_feeds(self, feed_ids):
        """Retrieves a list of feeds by id

        Creates GET request with single argument 'ids' formatted as 'ids={id1}+{id2}+...'

        Parameters
        ----------
        feed_ids : iterable
            an iterable of feed ids

        Returns
        -------
        list
            a list of :class:`RssFeed` objects

        Raises
        ------
        :class:`util.exceptions.HTTPBadRequest`
            indicates the api was used incorrectly
        :class:`RssApiError`
            indicates the feed retrieval failed
        """
        feed_ids = [str(x) for x in feed_ids]

        url = self._build_url(api=self.RSS_API, endpoint='retrievemany', ids='+'.join(feed_ids))

        resp = await self._single_get_request(url)

        if resp.status == 200:
            raw_feeds = await resp.json()

            feeds_out = []
            for rfeed in raw_feeds:
                feeds_out.append(self.build_feed(rfeed))
            return feeds_out
        elif resp.status == 400:
            raise HTTPBadRequest('Feed request error')
        else:
            raise RssApiError('Could not retrieve feeds for given channels')

    # POST method
    # May change name from update to get_update
    # Sends a list of feed ids and resource ids, receives a list
    # of updated feeds. This is the core RSS update method
    async def update_feeds(self, feeds):
        feeds_out = [x.brief() for x in feeds]

        url = self._build_url(api=self.RSS_API, endpoint='updatemany')

        resp = await self._single_post_request(url, json=feeds_out)

        if resp.status == 200:
            raw_feeds = await resp.json()

            return [self.build_feed(x) for x in raw_feeds]
        elif resp.status == 400:
            raise HTTPBadRequest('Feed update request error')
        else:
            raise RssApiError('Could not return feed updates for given channels')

    async def delete_feed(self, feed):
        url = self._build_url(api=self.RSS_API, endpoint='delete')

        resp = await self._single_post_request(url, json=feed)

        if resp.status == 200:
            deleted = await resp.json()

            return build_feed(deleted)
        elif resp.status == 400:
            raise HTTPBadRequest('Feed update request error')
        else:
            raise RssApiError('Could not return feed updates for given channels')

    def _build_url(self, api: str, endpoint: str, **args) -> str:
        """Constructs a request url for any api endpoint

        Follows the format https://{domain}/{endpoint}?{arg}={value}&{arg2}={value}

        Sample request:  https://bot.olliebot.cc/eb?img=no.png

        Parameters
        ----------
        endpoint : str
            the id of the api endpoint to access
        args : dict
            arguments to be written in `arg1=val&arg2=val` notation
        """

        if 'token' not in args:
            args['token'] = self.token
        return "{}{}?{}".format(api,
                                endpoint,
                                '&'.join(["{}={}".format(x, args[x]) for x in args if args[x] is not None]))

    def _build_json(self, **kwargs):
        return {k: v for (k, v) in kwargs.items() if v is not None}

    @staticmethod
    async def _get_json(page: str) -> dict:
        with aiohttp.ClientSession() as session:
            async with session.get(page) as resp:
                if resp.status == 200:
                    d = await resp.json()
                    return d

    @staticmethod
    async def _single_post_request(url: str, **kwargs):
        with aiohttp.ClientSession() as session:
            async with session.post(url, **kwargs) as resp:
                return resp

    @staticmethod
    async def _single_get_request(url: str):
        with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                return resp

    @staticmethod
    def build_feed(raw_feed: dict) -> RssFeed:
        feed_type = raw_feed['type']
        if feed_type == 'twitter':
            return TwitterFeed(**raw_feed)
        elif feed_type == 'twitch':
            return TwitchFeed(**raw_feed)
        elif feed_type == 'youtube':
            return YouTubeFeed(**raw_feed)
