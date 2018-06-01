# strawpoll module by CantSayIHave
# Created 2018/01/26
#
# Create polls because why do more work when the bot can
import json

import aiohttp


class StrawPoll:

    api_endpoint = 'https://www.strawpoll.me/api/v2/polls'
    dupcheck_options = ['normal', 'permissive', 'disabled']

    create_options = ['title', 'options', 'multi', 'dupcheck', 'captcha']

    def __init__(self, **kwargs):
        self.title = kwargs.get('title', 'no title')
        self.options = kwargs.get('options', [])
        self.multi = kwargs.get('multi', False)
        self.dupcheck = kwargs.get('dupcheck', 'normal')
        self.captcha = kwargs.get('captcha', False)
        self.id = kwargs.get('id', None)
        self.votes = kwargs.get('votes', [])

        if self.dupcheck not in self.dupcheck_options:
            self.dupcheck = 'normal'

    def edit(self, **kwargs):
        self.title = kwargs.get('title', self.title)
        self.options = kwargs.get('options', self.options)
        self.multi = kwargs.get('multi', self.multi)
        self.dupcheck = kwargs.get('dupcheck', self.dupcheck)
        self.captcha = kwargs.get('captcha', self.captcha)
        self.id = kwargs.get('id', self.id)
        self.votes = kwargs.get('votes', [])

        if self.dupcheck not in self.dupcheck_options:
            self.dupcheck = 'normal'

    def add_option(self, name: str = 'default'):
        self.options.append(name)

    async def create(self):
        if not self.title:
            raise(ValueError('Must have a title to create poll'))

        if not self.options:
            raise(ValueError('Must have at least two options to create a poll'))

        if self.id:
            raise(ValueError('Poll already exists'))

        print('Sent {}'.format(self.build_options()))

        with aiohttp.ClientSession() as session:
            async with session.post(url=self.api_endpoint, data=json.dumps(self.build_options())) as resp:
                if resp.status == 200:
                    j = await resp.json()
                    self.id = j.get('id', None)
                    return j
                try:
                    print('Received {}'.format(await resp.json()))
                except Exception:
                    print('Received {} - {}'.format(resp.status, await resp.text()))
                return False

    async def get(self):
        if not self.id:
            raise ValueError('Poll does not exist yet')

        with aiohttp.ClientSession() as session:
            async with session.get(url='{}/{}'.format(self.api_endpoint, self.id)) as resp:
                if resp.status == 200:
                    j = await resp.json()
                    self.edit(**j)
                    return j
                return False

    def build_options(self) -> dict:
        out_d = {}
        for k, v in self.__dict__.items():
            if k in self.create_options:
                out_d[k] = v
        return out_d
