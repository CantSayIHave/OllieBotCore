from datetime import datetime
import time

import discord
from discord.mixins import Hashable

import music_queue
from response import *
from util import global_util
from util.containers import *
from util.feeds import *


class Server(Hashable):
    """Holds bot data for a discord Server

    This class only shares the `str` 'id' with discord.Server objects

    This class needs to be cleaned up (useless members)

    """

    __slots__ = ['name', 'mods', 'feeds', 'spam_time', 'reee_message',
                 'id', 'rolemods', 'spam_timers', 'block_list', 'search_results',
                 'late', 'join_message', 'join_channel', 'leave_channel', 'message_changes',
                 'response_lib', 'music', 'capture', 'birthdays', 'default_role', 'selfroles']

    def __init__(self, **kwargs):
        self.name = kwargs.get('name', 'Default')
        self.mods = kwargs.get('mods', [])
        self.feeds = kwargs.get('feeds', [])  # type: list(RssFeed)
        self.spam_time = kwargs.get('spam_time', 1)
        self.reee_message = kwargs.get('reee_message', 'stop hitting yourself')
        self.id = kwargs.get('id', '')
        self.rolemods = kwargs.get('rolemods', [])
        self.spam_timers = kwargs.get('spam_timers', {})  # custom spam timed commands
        self.block_list = kwargs.get('block_list', [])
        self.search_results = None
        self.late = None

        self.default_role = kwargs.get('default_role', None)

        # a list of ids
        self.selfroles = kwargs.get('selfroles', [])
        if self.selfroles is None:
            self.selfroles = []

        # 12/13/17 update
        self.join_message = kwargs.get('join_msg', 'Welcome to the server, @u!')
        self.join_channel = kwargs.get('join_channel', '')

        self.leave_channel = kwargs.get('leave_channel', None)

        self.message_changes = kwargs.get('message_changes', None)

        self.response_lib = ResponseLibrary(self.spam_time)

        self.music = music_queue.MusicQueue(queue=kwargs.get('music_queue', []),
                                            bind_chat=kwargs.get('bind_chat', None))

        self.capture = None

        responses = kwargs.get('responses', None)
        if responses:
            for r in responses:
                self.response_lib.add(Response(**r))

        self.birthdays = kwargs.get('birthdays', [])

    def is_mod(self, user: discord.User):
        """Checks if user is a mod

        Parameters
        ----------
        user : :class:`discord.User`
            The user/member to test

        Returns
        -------
        bool
            Result of mod test
        """

        return user.id in self.mods

    def get_feed(self,
                 id=None,
                 discord_channel: discord.Channel = None,
                 type: str = None,
                 name: str = None,
                 channel_id: str = None,
                 search_lower: bool = False) -> RssFeed:
        """Searches for a feed based on name. `search_lower` searches lowercase of both

        Parameters
        ----------
        id : str
            the feed absolute id
        discord_channel : :class:`discord.Channel`
            query discord channel
        type : str
            type of feed
        name : str
            handle or username of feed
        channel_id : str
            id of query feed channel (if applicable)
        search_lower : bool
            a value of `True` will search lowercase

        Returns
        -------
        :class:`Feed`
            The found feed
        """
        if id:
            return global_util.iterfind(self.feeds, lambda x: x.id == id)

        if not name or channel_id:
            raise ValueError('Must provide feed name or channel id.')

        if not discord_channel:
            raise ValueError('Parameter searches need a discord channel')

        if search_lower:
            if not name:
                raise ValueError('Must provide a name to search lowercase.')

            name = name.lower()
            for feed in self.feeds:  # type: RssFeed
                if feed.name.lower() == name and feed.discord_channel_id == discord_channel.id:
                    if type:
                        if type == feed.string_type():
                            return feed
                    else:
                        return feed
        else:
            if name:
                for feed in self.feeds:  # type: RssFeed
                    if feed.name == name and feed.discord_channel_id == discord_channel.id:
                        return feed
            elif channel_id:
                for feed in self.feeds:  # type: RssFeed
                    if feed.channel_id == channel_id and feed.discord_channel_id == discord_channel.id:
                        return feed

    async def add_twitter_feed(self, channel: discord.Channel, handle: str):
        feed = await global_util.olliebot_api.create_twitter_feed(handle)
        feed.first_time = True
        feed.discord_channel_id = channel.id
        self.feeds.append(feed)
        return feed

    async def add_twitch_feed(self, channel: discord.Channel, username):
        feed = await global_util.olliebot_api.create_twitch_feed(username)
        feed.first_time = True
        feed.discord_channel_id = channel.id
        self.feeds.append(feed)
        return feed

    async def add_youtube_feed(self, channel: discord.Channel, username=None, channel_id=None):
        feed = await global_util.olliebot_api.create_youtube_feed(username=username, id=channel_id)
        feed.first_time = True
        feed.discord_channel_id = channel.id
        self.feeds.append(feed)
        return feed

    async def remove_feed(self, feed: RssFeed):
        deleted = await global_util.olliebot_api.delete_feed(feed)  # server copy
        self._delete_feed(deleted)  # client copy
        return deleted

    def add_birthday(self, user: discord.User, dt: datetime) -> Birthday:
        bd = Birthday(user=user, dt=dt)
        self.birthdays.append(bd)
        return bd

    def get_birthdays(self, date=None) -> list:
        """Returns all birthday objects matching a date"""
        if date:
            now = date
        else:
            now = datetime.utcfromtimestamp(time.time() - (4 * 3600))  # UTC - 4 = EST
        b_days = []
        for b in self.birthdays:  # type: Birthday
            if b.dt.day == now.day and b.dt.month == now.month:
                b_days.append(b)

        return b_days

    def get_birthday(self, user=None, date=None) -> Birthday:
        """Returns a single birthday object matching a user or date"""
        if user:
            for b in self.birthdays:  # type: Birthday
                if user == b.user:
                    return b
        elif date:
            for b in self.birthdays: # type: Birthday
                if date.day == b.dt.day and date.month == b.dt.month:
                    return b

    # deletes all instances
    def _delete_feed(self, feed: RssFeed):
        for f in self.feeds:
            if f.id == feed.id:
                self.feeds.remove(feed)