# music_queue module by CantSayIHave
# 2018/01/30
#
# revised music setup


import asyncio
from collections import deque

import discord
from discord.ext import commands

from util import global_util


class Track:
    def __init__(self, **kwargs):
        self.url = kwargs.get('url', '')
        self.requestee = kwargs.get('requestee', '')
        self.title = kwargs.get('title', '')

    def __repr__(self):
        return 'Track Object: {}'.format(self.__dict__)

    def __str__(self):
        return 'Track Object: {}'.format(self.__dict__)


class MusicQueue:
    def __init__(self, **kwargs):
        self.queue = deque([])
        in_queue = kwargs.get('queue', [])
        for t in in_queue:
            if type(t) is Track:
                self.queue.append(t)
            else:
                self.queue.append(Track(**t))

        self.bind_chat = kwargs.get('bind_chat', None)
        self.player = None
        self.autoplay_channel = None
        self.is_loading = False
        self.current_track = None
        self.vote_skip = None
        self.bot_voice_client = None
        self.bot = None

    def __len__(self):
        return len(self.queue)

    def __iter__(self):
        return iter(self.queue)

    def __next__(self):
        return self.queue.__next__()

    def __getitem__(self, item):
        return self.queue[item]

    def insert(self, i, O):
        self.queue.insert(i, O)

    def append(self, O):
        if not isinstance(O, Track):
            raise ValueError('Expected {}, got {}'.format(Track, type(O)))
        self.queue.append(O)

    def clear(self):
        self.queue.clear()

    def list(self):
        return [x.__dict__ for x in self.queue]

    def __repr__(self):
        return 'Music Queue: {}'.format(list(self.queue))

    def __str__(self):
        return 'Music Queue: {}'.format(list(self.queue))

    async def add_track(self, url: str, requestee: str):
        try:
            vid_id = self.yt_extract_id(url)
        except Exception as e:
            print('yt extract id failed at: {}'.format(e))
            return False
        if vid_id:
            vid = await global_util.yt.get_video_info(vid_id)  # type: dict
            if vid:
                t = Track(url=url, requestee=requestee, title=vid['snippet']['title'])
                self.queue.append(t)
                return t
        return False

    def add_track_raw(self, url: str, title: str, requestee: str) -> Track:
        t = Track(url=url, requestee=requestee, title=title)
        self.queue.append(t)
        return t

    def get_next_track(self) -> Track:
        try:
            self.current_track = self.queue.popleft()
            return self.current_track
        except IndexError:
            return None

    async def play_next(self, ctx, in_server, bot: commands.Bot):
        self.bot = bot

        if self.is_loading:  # set loading bool to prevent thread collisions
            return True
        self.is_loading = True

        try:
            voice_channel = ctx.message.author.voice_channel

            # IF:
            # - no voice client - not in voice channel
            # - but bot voice client exists AND user is high perm
            # so reg users can't use it from outta channel
            if not voice_channel:
                if not bot.has_high_permissions(ctx.message.author, in_server) or not self.bot_voice_client:
                    await bot.send_message(ctx.message.channel,
                                           'You are not in a voice channel. Please join one to call '
                                           '`{0}music play`'.format(bot.command_prefix))
                    self.is_loading = False
                    return False

            self.vote_skip_clear()

            if not self.bot_voice_client:
                self.bot_voice_client = bot.voice_client_in(ctx.message.server)

            if not self.bot_voice_client:
                self.bot_voice_client = await bot.join_voice_channel(voice_channel)

            next_up = self.get_next_track()
            if next_up:

                self.player = await self.bot_voice_client.create_ytdl_player(next_up.url,
                                                                             before_options="-reconnect 1",
                                                                             after=lambda: self.after(bot))

                self.player.start()

                self.autoplay_channel = ctx.message.channel

                await bot.send_message(ctx.message.channel,
                                       'Track `{}` enqueued by `{}` is now playing.'.format(next_up.title,
                                                                                            next_up.requestee))
            else:
                await bot.send_message(ctx.message.channel,
                                       'There are no songs in the queue. Add with '
                                       '`{0}music queue` or `{0}music play`'.format(bot.command_prefix))
        except Exception as e:
            print('MusicQueue play next exception: {}'.format(e))
        self.is_loading = False

    def pause(self):
        if self.player:
            self.player.pause()
            return True
        return False

    def unpause(self):
        if self.player:
            if not self.player.is_done() and not self.player.is_playing():
                self.player.resume()
                return True
        return False

    def is_playing(self):
        if self.player:
            if not self.player.is_done() and self.player.is_playing():
                return True
        return False

    def after(self, bot: commands.Bot):
        self.vote_skip_clear()
        next_up = self.get_next_track()
        if next_up:
            if self.is_loading:
                return True
            self.is_loading = True
            coro = self.bot_voice_client.create_ytdl_player(next_up.url,
                                                            before_options="-reconnect 1",
                                                            after=lambda: self.after(bot))
            fut = asyncio.run_coroutine_threadsafe(coro, bot.loop)

            self.player = None
            try:
                self.player = fut.result()
            except Exception:
                pass

            if not self.player:
                print('Music player creation error - After function')
                self.is_loading = False
                return False

            self.player.start()
            self.player.volume = 1.0

            coro = bot.send_message(self.autoplay_channel,
                                    'Track `{}` enqueued by `{}` is now playing.'.format(next_up.title,
                                                                                         next_up.requestee))
            fut = asyncio.run_coroutine_threadsafe(coro, bot.loop)

            try:
                fut.result()
            except Exception:
                pass

            self.is_loading = False
            return True
        else:
            global_util.schedule_future(self.check_timeout(), time=30)  # register disconnect check
            return False

    def vote_skip_clear(self):
        self.vote_skip = None

    def vote_skip_register(self, member: discord.Member):
        if not self.vote_skip:
            self.vote_skip = []
        if member.id not in self.vote_skip:
            self.vote_skip.append(member.id)
            return True
        return False

    def vote_skip_check(self, channel: discord.Channel):
        if channel.type != discord.ChannelType.voice and channel.type != 'voice':
            return None
        if not self.vote_skip:
            return None
        if not channel.voice_members:
            return None
        if len(channel.voice_members) < 1:
            return None
        if (len(self.vote_skip) / (len(channel.voice_members) - 1)) >= (2 / 3):
            self.vote_skip = None
            return True
        return False

    async def skip(self):
        self.vote_skip_clear()
        if self.player:
            self.player.stop()

    @staticmethod
    def yt_extract_id(url: str):
        if 'youtube' in url and 'v=' in url:
            v_tag = url.rsplit('v=', 1)
            return v_tag[1].split('&')[0]
        elif 'youtu.be' in url:
            return url.rsplit('/', 1)[1]
        return None

    async def auto_disconnect(self):
        on_vc = self.bot_voice_client
        if on_vc:
            try:
                self.player.stop()
            except AttributeError:
                print('-No player to stop.')
            vc_name = on_vc.channel.name
            await on_vc.disconnect()

            await self.bot.send_message(self.autoplay_channel,
                                        'Disconnected from voice channel `{}` due to inactivity'.format(vc_name))

            self.player = None
            self.autoplay_channel = None
            self.bot_voice_client = None
            return True
        else:
            return False

    async def check_timeout(self):
        if not self.is_playing():
            await self.auto_disconnect()

