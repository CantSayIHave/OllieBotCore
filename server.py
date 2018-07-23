from datetime import datetime
import time

import discord
from discord.mixins import Hashable

import music_queue
from response import *
from util import global_util
from util.containers import *


class Server(Hashable):
    """Holds bot data for a discord Server

    This class only shares the `str` 'id' with discord.Server objects

    This class needs to be cleaned up (useless members)

    """

    __slots__ = ['name', 'mods', 'commands', 'rss', 'command_delay', 'reee_message',
                 'id', 'reee', 'rolemods', 'spam_timers', 'block_list', 'bot_voice_client',
                 'search_results', 'suggest_emotes', 'music_player', 'music_chat', 'music_channel',
                 'music_loading', 'music_timer', 'late', 'current_track', 'vote_skip', 'join_message',
                 'join_channel', 'leave_channel', 'response_lib', 'music', 'capture', 'birthdays']

    def __init__(self, **kwargs):
        self.name = kwargs.get('name', 'Default')
        self.mods = kwargs.get('mods', [])
        self.commands = kwargs.get('commands', [])
        self.rss = kwargs.get('rss', [])
        self.command_delay = kwargs.get('command_delay', 1)
        self.reee_message = kwargs.get('reee_msg', 'stop hitting yourself')
        self.id = kwargs.get('id', '')
        self.reee = kwargs.get('reee_state', True)
        self.rolemods = kwargs.get('rolemods', [])
        self.spam_timers = kwargs.get('spam_timers', {})  # custom spam timed commands
        self.block_list = kwargs.get('block_list', [])
        self.bot_voice_client = None  # actual voice client - for autoplay
        self.search_results = None
        self.suggest_emotes = []
        # self.music = deque(kwargs.get('queue', []))
        self.music_player = None
        self.music_chat = kwargs.get('music_chat', None)
        self.music_channel = None  # chat channel player is bound to - for autoplay
        self.music_loading = False
        self.music_timer = None  # timer for client disconnect
        self.late = None
        self.current_track = None
        self.vote_skip = None

        # todo: rename rss to feeds (everywhere) and destroy commands
        # todo: rename command_delay to spam_time

        # 12/13/17 update
        self.join_message = kwargs.get('join_msg', 'Welcome to the server, @u!')
        self.join_channel = kwargs.get('join_channel', '')

        self.leave_channel = kwargs.get('leave_channel', None)

        self.response_lib = ResponseLibrary(self.command_delay)

        self.music = music_queue.MusicQueue(queue=kwargs.get('queue', []), bind_chat=kwargs.get('music_chat', None))

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

    def music_timeout(self):
        """Manages music timeout measurement when called.

        Returns
        ---------
        bool
            an indicator to close the music connection - 'True' or 'False'
        """

        if self.music_timer is None:
            self.music_timer = 0
            return False
        else:
            self.music_timer += 10

            if self.music_timer >= global_util.TIME_MUSIC_TIMEOUT:
                self.music_timer = None
                return True
            return False

    def get_rss(self, discord_channel: discord.Channel, uid: str = None, title: str = None, wide_search: bool = False) -> Feed:
        """Searches for a feed based on uid or title. `wide_search` searches lowercase of both

        Parameters
        -----------
        discord_channel : str
            id of query discord channel
        uid : str
            id of query feed
        title : str
            title of query feed
        wide_search : bool
            indicates search type. A value of `True` will search both uid and title lowercase

        Returns
        ---------
        :class:`Feed`
            The found feed
        """

        if wide_search:
            if uid:
                query = uid
            elif title:
                query = title
            else:
                raise ValueError('Must provide a query.')
            query = query.lower()

            for r in self.rss:  # type: Feed
                if (r.uid.lower() == query or r.title.lower() == query) and r.channel_id == discord_channel.id:
                    return r
        else:
            if uid:
                for r in self.rss:  # type: Feed
                    if r.uid == uid and r.channel_id == discord_channel.id:
                        return r
            elif title:
                for r in self.rss:  # type: Feed
                    if r.title == title and r.channel_id == discord_channel.id:
                        return r
            else:
                raise ValueError('Must provide a query.')

    def add_birthday(self, user: discord.User, dt: datetime):
        bd = Birthday(user=user, dt=dt)
        self.birthdays.append(bd)
        return bd

    def get_birthdays(self, date=None):
        if date:
            now = date
        else:
            now = datetime.utcfromtimestamp(time.time() - (4 * 3600))  # UTC - 4 = EST
        b_days = []
        for b in self.birthdays: # type: Birthday
            if b.dt.day == now.day and b.dt.month == now.month:
                b_days.append(b)

        return b_days

    def get_birthday(self, user=None, date=None):
        if user:
            for b in self.birthdays:  # type: Birthday
                if user == b.user:
                    return b
        elif date:
            for b in self.birthdays: # type: Birthday
                if date.day == b.dt.day and date.month == b.dt.month:
                    return b
