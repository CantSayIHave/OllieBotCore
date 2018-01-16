# Twitch API wrapper for getting channels and scraping streams
# Created by CantSayIHave, 8/19/2017
# Open source

import requests
import json
import asyncio
import aiohttp


async def create(client_id: str, client_secret: str, oauth: str = None):
    twitch = TwitchRss(client_id, client_secret, oauth)
    await twitch.initialize()
    return twitch


class TwitchRss:

    v5_api = 'application/vnd.twitchtv.v5+json'

    def __init__(self, client_id: str, client_secret: str, oauth: str = None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.oauth_token = oauth

    async def initialize(self):
        if not self.oauth_token:
            self.oauth_token = await self.get_new_token()
        else:
            auth = await self.check_auth()
            if not auth:
                self.oauth_token = await self.get_new_token()

    async def get_new_token(self):
        async with aiohttp.post('https://api.twitch.tv/kraken/oauth2/token' +
                          '?client_id={}'.format(self.client_id) +
                          '&client_secret={}'.format(self.client_secret) +
                          '&grant_type=client_credentials') as p:
            if p.status == 200:
                auth = await p.json()
                return auth['access_token']
            else:
                raise ValueError('Auth request failed')

    async def check_auth(self):
        async with aiohttp.get('https://api.twitch.tv/kraken', headers=self.build_header()) as r:

            if r.status == 200:
                auth = await r.json()
                return auth['token']['valid']
            else:
                raise ValueError('TwitchAPI: Auth check failed, HTTP code {0}'.format(r.status))

    def build_header(self):
        h = {'Accept': self.v5_api,
             'Client-ID': self.client_id,
             'Authorization': 'OAuth {0}'.format(self.oauth_token)}
        return h

    async def get_channel_from_name(self, name: str):
        self.get_auth()
        async with aiohttp.get('https://api.twitch.tv/kraken/users?login={0}'.format(name),
                               headers=self.build_header()) as r:

            if r.status == 200:
                channel = await r.json()
                if channel['_total'] == 1:
                    return channel['users'][0]
                return None
            else:
                raise ValueError('Channel request failed')

    async def get_channel(self, _id: str):
        self.get_auth()
        async with aiohttp.get('https://api.twitch.tv/kraken/channels/{0}'.format(_id),
                               headers=self.build_header()) as r:

            if r.status == 200:
                return await r.json()
            elif r.status == 404:
                return None
            else:
                raise ValueError('Channel request failed')

    async def get_stream(self, channel_id: str):
        self.get_auth()
        async with aiohttp.get('https://api.twitch.tv/kraken/streams/{0}'.format(channel_id),
                               headers=self.build_header()) as r:

            if r.status == 200:
                stream = await r.json()
                if stream['stream']:
                    return stream
                return None
            else:
                raise ValueError('Stream request failed')

    def get_auth(self):
        auth = yield from self.check_auth()
        if not auth:
            self.oauth_token = self.get_new_token()
